[![build](https://github.com/i-dot-ai/orbit/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/i-dot-ai/orbit/actions/workflows/build.yml?query=branch%3Amain)

# orbit

## Development

#### Setup Application

* Install the following packages:

```bash
brew install uv
```

Next, edit the variables in `.env` to have the values you need. Replace the following  in the `.env` file.

 - `account_id` with your AWS account ID. If you are unsure about the account ID, please reach out to your team members for assistance.
 - `auth_api_url` with an example value of `http://auth-url.local` for local environment. This URL will be obtained from SSM Parameter Store by the Terraform when creating the ECS Task Definition.

We use [uv](https://github.com/astral-sh/uv) to manage our Python packages. uv uses the project root level `pyproject.toml` to store information about the project and packages.

To set up the python environment for development:

``` bash
make install
```

When executing any python command, prefix with `uv run` to run it in the uv environment. e.g. `uv run python -m pytest`.

To add new packages, edit `pyproject.toml` and run `uv lock` to update the lock file.

To run the test locally use following command:

``` bash
make test
```

#### Running application locally



To run the backend application, use the following command:

```bash
make run_backend
```

The backend application will start on [http://127.0.0.1:8000](http://127.0.0.1:8000). Once the backend process is up and running, set the environment variable to be used by the frontend application to communicate with the backend service:

```bash
export BACKEND_HOST=http://127.0.0.1:8000
```

To run the frontend application, use the following command:

```bash
make run_frontend
```

Open [http://localhost:3000](http://localhost:3000) in your browser to see the result.







#### Local Development



This can be done by running either the backend or frontend individually, or by running both concurrently with `docker-compose up`.

``` bash
make docker_build_local service=frontend
make docker_build_local service=backend
```

#### Communication between services

The frontend should expect an environment variable called `BACKEND_HOST` and make calls to the backend using this variable.

The way that we get around CORS issues atm is by having the frontend server make requests to the backend API.




#### Enabling Backend Programmatic Access

Using AWS WAF we're now able to enable access directly to your backend containers directly from the internet (if your IP address is allowed!) <br>

###### When should you use this?

If you have a requirement of giving access to one to many applications directly as an API or an MCP server, without going through the frontend. A few I.AI examples of this are:

- Parliament MCP
- Parlex Backend as an API
- Caddy Backend as an API

With the WAF config, you can onboarded one to many clients and have seperate tokens for each. An example of this is having `gov-ai` connecting to one-to-many MCP clients using the backend programatic access.

An example connecting via a config file in [gov-ai](https://github.com/i-dot-ai/gov-ai-client/blob/main/.mcp-servers-example.yaml#L10-L13) and in [code](https://github.com/i-dot-ai/gov-ai-client/blob/main/frontend/src/logic/get-tools.ts#L31)


###### How to enable backend-access:
To enable this backend programmatic access, add the following configuration to `load_balancer.tf` under the `waf` module, specifically the `header_secured_access_configuration`

```terraform
host_backend      = terraform.workspace == "prod" ? "${var.project_name}-backend-external.i.ai.gov.uk" : "${var.project_name}-backend-external-${terraform.workspace}.i.ai.gov.uk"

module "waf" {
  # checkov:skip=CKV_TF_1: We're using semantic versions instead of commit hash
  # source        = "../../i-dot-ai-core-terraform-modules//modules/infrastructure/waf" # For testing local changes
  source         = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/waf?ref=v7.0.0-waf"
  name           = local.name
  host           = local.host
  env            = var.env

  header_secured_access_configuration = {
    kms_key_id = data.terraform_remote_state.platform.outputs.kms_key_arn
    hostname = local.host_backend
    client_configs = [
      {
        client_name = "example-client-name",
      },
      {
        client_name = "example-client-name-2",
      }
    ]
  }
}
```

This creates a new rule on the attached WAF to your application which allows these specific clients to connect directly to your backend container using the new endpoint of:`$app-name-backend-external.i.ai.gov.uk`<br>

The WAF module will create a token for each of the clients you've created and store these value in AWS Param Store. The WAF Token (used similar to an API Key) can be used in the request to your backend container:
```sh
curl -X 'GET' 'https://$app-name-backend-external.i.ai.gov.uk/healthcheck' -H 'accept: application/json' -H 'x-external-access-token: example_client_name-RANDOM_STRING'
```

## Deployment

When you cut and deploy your application, it will initially be available at the following addresses in the different environments:
- Dev - `https://orbit.internal.dev.i.ai.gov.uk`
- Preprod - `https://orbit.internal.preprod.i.ai.gov.uk`
- Prod - `https://orbit.internal.i.ai.gov.uk`

Applications can also be added to the i.AI Edge Network, which will provide a public-facing (i.e. non-whitelisted) URL for production:
- Dev - `https://orbit.dev.i.ai.gov.uk`
- Preprod - `https://orbit.preprod.i.ai.gov.uk`
- Prod - `https://orbit.i.ai.gov.uk`

> Note: All three "Edge" URLs will be created, but only the production URL will have the whitelist removed.

Further information on creating public-facing URLs for your application is available in the [Edge Network repository readme](https://github.com/i-dot-ai/core-edge-network/). 

<details>
  <summary>Click to expand the AWS architecture diagram</summary>

  ![AWS architecture diagram](aws_architecture.jpg)

</details>

### Users

To create users for your app, you'll need to add them to our Auth API deployment. The documentation for that can be found in the core-auth-api repo.

When Auth API has been updated with the user(s), the added user(s) will get an email with their credentials to access the app.

### CI/CD

#### Builds

The docker images for the services will be built on every push to any branch by the github actions.

#### Releases

The first release to any environment will have to be done manually - contact an admin to make this happen. The admin will need to follow the following process:

- Deploy the `ECR` manually using the `core-infra` repo's `universal` instance.
- Deploy the project specific infra using the `tf_apply` command for `dev`, `preprod`, and `prod`.
- [Add](https://github.com/i-dot-ai/i-ai-core-infrastructure/blob/main/instances/platform/github_roles.tf#L4-L18) project to `github_deploy_roles` for each environment.

Subsequent releases will be done automatically by the GitHub actions. They are triggered by:

- Running `make release env=<env>` to release any commit to `dev` or `preprod`.
- Pushing to main will release to `prod`.

#### Notifications

The CI/CD pipeline is configured to send Slack notifications when a deployment to a given environment occurs. This process uses the `SLACK_WEBHOOK_URL` GitHub secret to post the message to Slack. By default, a repo will use the GitHub secret located at the organisation level to post the message to the `#platform-release-notifications-test` channel. 

To override this behaviour so the message posts to a channel of your choosing, follow these instructions:
- Proceed to the [GitHub Notification](https://api.slack.com/apps/A07CA1KSF8Q/incoming-webhooks) Slack app webhooks page and select "add new webhook to workspace"
- On the next page, select the Slack channel you want to add the webhook to and click "Allow".
- Copy the webhook link provided and add this as a GitHub Actions secret in the repository of choice. Slack notifications for this repo will now be directed to this channel.

### Slack Notifications for CloudWatch Alarms

The CI/CD pipeline is set up to send notifications to specific Slack channels when CloudWatch Alarms are triggered. Notifications will be sent to environment-specific channels as follows:

- **Prod**: `#application-alerts`
- **Preprod**: `#application-alerts-preprod`
- **Dev**: `#application-alerts-dev`

#### Customizing Notification Channels

If you need to change the default channel for notifications, follow these steps:

1. Go to the [GitHub Notification](https://api.slack.com/apps/A07JPB123B8/incoming-webhooks) Slack app webhooks page and select **"Add new webhook to workspace."**
2. On the next screen, choose the Slack channel where you want the notifications to be sent and click **"Allow."**
3. Copy the provided webhook URL and update the `slack_webhook` variable in your Terraform configuration.

### Sentry setup

To set up sentry, login to our organisation account at [sentry.io](sentry.io).

- Navigate to the `projects` page
- Click `Create project`
- Select `FASTAPI` as project type
- Click create
- On the following page, in the `Configure SDK`, copy the value for `dsn=` **KEEP THIS SECRET**
- Navigate to the SSM parameter store entry for your deployed application
- Replace `SENTRY_DSN` value with the value you copied


### Environment Variables

#### Non-sensitive

For non-secret environment variables, they can be passed into the applications in plain-text and passed into the environment variables argument of the relevant service in `terraform/ecs.tf`.

#### Sensitive

For sensitive environment variables, an SSM Parameter Store parameter can be created for each secret required by your application. 

The parameters are stored as encrypted secure strings with SSM Parameter Store, and match the following shape:
`/i-dot-ai-<env>-<app-name>/env_secrets/<variable-name>`

These secrets can be created or removed as required by updating `terraform/secrets.tf`. Secret values must not be hardcoded here - they should either be set as references, or deployed with a placeholder value and subsequently updated in SSM.

Any secrets defined here will be read from SSM securely and loaded into the container on initialisation. From this point onwards, they are accessible as any other environment variable as `<variable-name>`.

Secrets can be updated in SSM by navigating to SSM Parameter Store in the AWS console, finding the desired variable, and editing the value. Production variables cannot be viewed by non-admins for security reasons, but can still be set by calling PutParameter using the AWS CLI, replacing `name` and `value` as appropriate:
```aws ssm put-parameter \
    --name "/i-dot-ai-<env>-<app-name>/env_secrets/<variable-name>" \
    --value "<new-value>" \
    --type "SecureString" \
    --overwrite
```

### Data

An S3 bucket will have been created for your application per environment. This can be used to store any data that your application needs to persist. It will be called: `i-dot-ai-<env>-orbit-data`

## Database

orbit uses a persistent data store using postgresql, running in a docker container locally (called `db`), and using aurora when deployed to aws.

Models for the database are kept in `orbit/database/postgres_models.py`.

Pydantic models for the database interaction are kept in `orbit/database/pydantic_schemas.py`.

A function interface for interacting with the database is kept in `orbit/database/postgres_interface.py`.

We use SQLAlchemy for database connections, and alembic for tracking migrations. The `alembic.ini` file at the root of the project handles alembic configuration and the connection string to the db to action against.

When adding new models, import each model into `alembic/env.py` so that alembic reads it into the config.

Run `uv run alembic revision --autogenerate` to generate a new migration, and `uv run alembic upgrade head` to run the upgrade to apply the new migration.


### Debugging

#### Getting to the logs

To get the logs of your apps for any issues, you can do the following:

- Login to the AWS Console
- Navigate to ECS
- Select Clusters
- Select your cluster: `i-dot-ai-<env>-orbit-cluster`

- Select your service: `i-dot-ai-<env>-orbit-<frontend/backend>-service`

- Select the logs tab (you can also click view in cloudwatch for a more details breakdown)

#### Getting into the container

To get into the running container, you need to:

- Get to the service in the AWS console, the last step in [getting to the logs](#getting-to-the-logs).
- Select a running task
- Get the ARN of the task, it's within the Task overview section of the task Configuration tab.
- Execute the command below (ensuring you are authenticated with AWS):
```
aws ecs execute-command \
    --cluster i-dot-ai-<env>-cluster \
    --task <TASK_ARN> \
    --interactive \
    --command "/bin/sh"
```
> Note: You will only have permissions to do this on tasks in dev or preprod environments.

#### Diagrams Module Dependency

The `diagrams` module is used in the `orbit/terraform/diagram_script.py` file. To generate the `diagrams`, follow the instructions below:

``` bash
make generate_aws_diagram
```

