# S3 Annotations Demo

Serverless pipeline that copies volcano camera images from the last 7 UTC days of
[**GeoNet Aotearoa New Zealand Data**](https://registry.opendata.aws/geonet/)
(`s3://geonet-open-data`, AWS Open Data Sponsorship Program), writes metadata via
Amazon S3 Annotations, and serves a filterable image gallery through an
AWS Amplify-hosted React SPA.

All cloud resources are provisioned with Terraform and removed with a single
`terraform destroy`.

**Presenter guide:** [docs/walkthrough.md](docs/walkthrough.md)

## Architecture

See **[docs/walkthrough.md](docs/walkthrough.md#architecture)** for the diagram and component table.

```text
GeoNet open data → Ingest Lambda → Private S3 (+ S3 Annotations)
                                        ↓
Amplify gallery ← API Gateway ← API Lambda (reads annotations)
```

| Component | AWS Service | Purpose |
| --------- | ----------- | ------- |
| Scheduler | EventBridge Scheduler | One-time trigger for ingest pipeline |
| Ingest Lambda | Lambda (Python 3.14) | Copy images, derive tags, write annotations |
| API Lambda | Lambda (Python 3.14) | Query annotations, filter, return presigned URLs |
| HTTP API | API Gateway v2 | Expose GET /images endpoint with CORS |
| Frontend | Amplify Hosting | Host React SPA |
| DynamoDB (optional) | DynamoDB | Fast indexed queries when enabled |

## Prerequisites

- AWS account with permissions to create the resources above
- [Terraform](https://www.terraform.io/) ≥ 1.6
- Node.js + npm (Amplify frontend build on apply)
- Python **3.14** (`python3.14`) for Lambda development and tests — matches the `python3.14` Lambda runtime
- AWS CLI, `curl`, and `zip` (Amplify deployment step)
- `pip3` (bundles boto3 ≥ 1.43 into Lambda packages on apply — required for S3 Annotations API)

## Apply Flow

Deploy the full stack (no scheduler by default — no prompts):

```bash
cd terraform
terraform init
terraform apply
```

After apply, Terraform automatically **builds and deploys** the React app to
Amplify (`deploy_amplify_on_apply = true` by default). That avoids the
Amplify **Welcome** placeholder page — open the URL from output
`amplify_app_url`, click **Apply Filters**, and load images.

To skip the frontend deploy (e.g. CI without Node.js):

```bash
terraform apply -var='deploy_amplify_on_apply=false'
./scripts/deploy-amplify.sh   # run manually later with env vars set
```

To **also** schedule a one-time ingest run, opt in with a future UTC time:

```bash
terraform apply \
  -var='enable_scheduler=true' \
  -var='schedule_time=2026-06-19T08:00:00'
```

Or copy `terraform/terraform.tfvars.example` to `terraform.tfvars`, uncomment
`enable_scheduler` and `schedule_time`, then run `terraform apply`.

> **Note:** `schedule_time` must be a future UTC datetime:
> `YYYY-MM-DDTHH:mm:ss`. The scheduler fires once and auto-deletes.

## Ingest: scheduled vs manual

| Method | When to use |
| ------ | ----------- |
| **Manual invoke** | Run ingest immediately (demo/testing) |
| **Scheduler** | Fire ingest once at a chosen UTC time |

Manual invoke (no Terraform vars):

```bash
aws lambda invoke \
  --function-name volcano-ingest \
  --payload '{}' \
  --cli-binary-format raw-in-base64-out \
  /tmp/ingest-result.json
```

## One-Time Scheduler Notes

- Scheduler is **off by default** (`enable_scheduler = false`) so
  `terraform apply` and `terraform destroy` never ask for `schedule_time`.
- When enabled, EventBridge fires **once** at `schedule_time` and
  auto-deletes (`action_after_completion = DELETE`).
- To schedule another run after the first fires: set a new `schedule_time`
  and `terraform apply` again (Terraform recreates the schedule).

## Configuration Variables

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `aws_region` | AWS region for all resources | `ap-southeast-2` |
| `enable_scheduler` | Create one-time EventBridge ingest schedule | `false` |
| `deploy_amplify_on_apply` | Build and deploy frontend after apply | `true` |
| `schedule_time` | UTC datetime when scheduler enabled | `2099-01-01T00:00:00` (ignored if scheduler off) |
| `enable_dynamodb` | Enable DynamoDB table for fast annotation queries | `false` |
| `amplify_app_name` | Name for the Amplify application | `volcano-annotations-demo` |

## Teardown

Remove **all** resources with a single command:

```bash
cd terraform
terraform destroy -auto-approve
```

All resources are Terraform-managed. `force_destroy = true` on the S3 bucket
means no manual cleanup is needed — non-empty buckets are emptied and deleted
automatically.

Resources removed by `terraform destroy`:

- Private S3 bucket (including all objects)
- Amplify Hosting application
- Ingest Lambda and API Lambda
- API Gateway HTTP API
- EventBridge Scheduler (if it hasn't auto-deleted yet)
- IAM roles and policies
- DynamoDB table (when enabled)

> The EventBridge Scheduler auto-deletes after execution via
> `action_after_completion = DELETE`. If you run `terraform destroy` before
> the scheduler fires, Terraform removes it directly. Either way, no
> dangling resources remain.

## Optional Verification

After teardown, confirm all resources are gone:

```bash
terraform state list  # should be empty after destroy
```

## Sample Images

Local reference samples (TKAH.01, UTC day 169):

- `samples/volcano/2026.169.0240.00.TKAH.01.jpg`
- `samples/volcano/2026.169.0800.00.TKAH.01.jpg`

Source: `s3://geonet-open-data/camera/volcano/images/2026/TKAH/TKAH.01/2026.169/`

## Testing

Use Python 3.14 locally (same as Lambda runtime):

```bash
python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest tests/ -v
```

Tests include property-based tests (via Hypothesis) for the classifier,
key parser, and API validator, plus unit tests for Lambda handlers.
