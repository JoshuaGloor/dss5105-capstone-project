# Deploying the app

Two containers on one EC2 instance: the Streamlit app, and Caddy in front of it.
Images live in ECR. GitHub Actions builds on merge and deploys on demand, over
SSM, so there is no SSH and no AWS key stored anywhere.

The instance is stopped when not needed (to save cost), so the usual sequence is
start, deploy, stop.

## Day to day

In the repo's Actions tab:

1. **Power** -> Run workflow -> `start`. The summary prints the URL. Containers
   come back on their own, so this alone is enough to show the current build.
2. **Deploy app** -> Run workflow, tag empty, if you want to ship newer code.
3. **Power** -> Run workflow -> `stop` when you are done.

To roll back, run **Deploy app** with an older commit SHA in `tag`. We keep the
last few images in ECR, otherwise you have to use the Git history to rebuild the
image.

The site is behind a password (`infra/Caddyfile`). To change it (e.g., if you
are not part of the team and do not know the password but want to try out the
deploy):

```bash
{docker | podman} run --rm docker.io/library/caddy:2 caddy hash-password --plaintext 'new-password'
```

Paste the hash into the `basic_auth` block in the `infra/Caddyfile` and deploy.

## Changing the model or the API key

Both live in one SSM SecureString, `/dss5105/prod/env`, holding a dotenv blob.
The instance reads it with its own role at deploy time and compose hands it to
the app as `.env.secrets`.

The parameter can be replaced as in the below example:

```bash
cat > /tmp/env <<'ENV'
LLM_MODEL=anthropic:claude-sonnet-5
ANTHROPIC_API_KEY=sk-ant-...
ENV
aws ssm put-parameter --region ap-southeast-1 --name /dss5105/prod/env \
  --type SecureString --value file:///tmp/env --overwrite && rm /tmp/env
```

Then **Power** -> `start` if the instance is stopped, and **Deploy app** with
`tag` empty.

Only the key matching the `LLM_MODEL` provider prefix is needed. Both providers
ship in the image, so moving between `anthropic:` and `openai:` is a parameter
change and a deploy, with no rebuild.

Smoke-test by typing a natural-language order on the desk.

## Saved allocations

Confirmed allocations, the desk's live queue state, and the dispatcher's
remembered profile and standing rules live in SQLite, in a docker volume on the
instance. They survive deploys, reboots, and Power stop/start.

They are lost if the instance is **replaced**, which only an infrastructure
change can cause: editing `infra/tofu/user_data.sh` or `docker_compose_version`,
or running `tofu destroy`. No workflow can do it, and `tofu plan` says when a
change would replace the instance. Export both from the app first:
**Export saved allocation records** on the desk, and **Export memory** on the
Memory page's Log tab.

## Clearing saved allocations

The app does it on its own: **Memory -> Plan -> Start a fresh demo plan**, tick
the confirmation, then **Archive and start fresh**. The current plan moves to
`runtime/archive` and the queues restart from the course snapshot, while
standing rules and the log stay. Use this before a demo or a recording.

## Clearing remembered memory

Standing rules, the conversation log and the dispatcher profile (and potentially more
in the future) are `runtime/memory.sqlite3`, and no page deletes them (as of now).
Export from **Memory -> Log -> Export memory** first if you want to keep the record, then
go in over Session Manager.

```bash
INSTANCE_ID=$(aws ec2 describe-instances --region ap-southeast-1 \
  --filters "Name=tag:Project,Values=dss5105" "Name=instance-state-name,Values=running" \
  --query 'Reservations[0].Instances[0].InstanceId' --output text)
aws ssm start-session --region ap-southeast-1 --target "$INSTANCE_ID"
```

The deploy writes `/opt/app/.env` as root with mode 600, and compose reads it before
anything else, so without `sudo` you get a `permission denied`.

Clearing memory only, leaving bookings and queues alone:

```bash
sudo docker exec dss5105-app-1 rm -f /app/runtime/memory.sqlite3
```

Safe while the app is running: the tables are recreated on the next page load.

Clearing memory, bookings and archives together, back to a blank instance:

```bash
sudo docker compose -f compose.yaml -f compose.prod.yaml down
sudo docker volume rm dss5105_app_runtime
sudo docker compose -f compose.yaml -f compose.prod.yaml up -d
```

This also discards `runtime/dispatch.sqlite3` and `runtime/archive`, so the
queues restart from the course snapshot.

## Local development

```bash
cp .env.example .env # set LLM_MODEL and one provider key
cd infra
{docker | podman} compose up --build
```

Open <http://localhost:8080> and click something.

The API key is currently optional: without it everything works except natural-language intake.

## First-time setup

Only needed once, or to rebuild from scratch. Requires the AWS CLI, an AWS account, and OpenTofu.

```bash
# 1. State bucket, GitHub OIDC provider, deploy role.
cd infra/tofu/bootstrap && tofu init && tofu plan && tofu apply

# 2. The app's secrets. Never put these in the repo or in tofu.
cat > /tmp/env <<'ENV'
LLM_MODEL=anthropic:claude-opus-4-8
ANTHROPIC_API_KEY=...
ENV
aws ssm put-parameter --region ap-southeast-1 --name /dss5105/prod/env \
  --type SecureString --value file:///tmp/env && rm /tmp/env

# 3. ECR, security group, instance. Paste the bootstrap state_bucket output
#    into the backend block in main.tf first.
cd ../ && tofu init && tofu plan && tofu apply
```

Then set two repo variables under Settings -> Secrets and variables -> Actions:
`AWS_REGION` (`ap-southeast-1`) and `AWS_DEPLOY_ROLE_ARN` (the bootstrap output).
Leave `SITE_ADDRESS` unset until you have a domain; set it to one and Caddy
obtains a certificate by itself. Our deployment keeps a domain there, and the
assistant's voice input depends on it: browsers only expose the microphone on a
secure origin, so on a plain-HTTP address the app is typing-only.

Rotating the key or changing the model later needs no repo change: see
[Changing the model or the API key](#changing-the-model-or-the-api-key).

## Troubleshooting

- **"No running instance"**: run Power -> start.
- **"The language model is unavailable"**: the app only works on models where
  thinking is off by default (currently). Opus 5 and newer fail, because structured
  output forces a tool call and those models reject it.
- **The microphone is blocked, or the button says voice needs another browser**:
  speech recognition needs a secure origin and a browser that has it (Chrome, Edge
  or Safari). Check that `SITE_ADDRESS` still names the domain, so Caddy serves
  HTTPS rather than the bare IP. See [VOICE_ASSISTANT.md](VOICE_ASSISTANT.md).

## Teardown

Do this after the project is over to cleanup everything on AWS.
Until then, we keep the elastic IP which makes things simpler.

```bash
cd infra/tofu && tofu destroy
cd bootstrap && tofu destroy
aws ssm delete-parameter --region ap-southeast-1 --name /dss5105/prod/env
```
