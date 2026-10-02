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

## Saved allocations

Confirmed allocations and the desk's live queue state live in SQLite, in a
docker volume on the instance. They survive deploys, reboots, and Power
stop/start.

They are lost if the instance is **replaced**, which only an infrastructure
change can cause: editing `infra/tofu/user_data.sh` or `docker_compose_version`,
or running `tofu destroy`. No workflow can do it, and `tofu plan` says when a
change would replace the instance. Export the records from the app first
(**Export saved allocation records**).

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
obtains a certificate by itself.

Rotating the key later is step 2 with `--overwrite`, then a deploy. No repo change.

## Troubleshooting

- **"No running instance"**: run Power -> start.
- **"The language model is unavailable"**: the app only works on models where
  thinking is off by default (currently). Opus 5 and newer fail, because structured
  output forces a tool call and those models reject it.

## Teardown

Do this after the project is over to cleanup everything on AWS.
Until then, we keep the elastic IP which makes things simpler.

```bash
cd infra/tofu && tofu destroy
cd bootstrap && tofu destroy
aws ssm delete-parameter --region ap-southeast-1 --name /dss5105/prod/env
```
