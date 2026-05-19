# ☁️ Quantum Mind — Complete AWS Production Deployment Playbook

This document details the exact checklist, prerequisites, architecture configuration, and command pipeline required to launch the **Quantum Mind** backend completely live on Amazon Web Services (AWS) using **ECS Fargate, RDS PostgreSQL, ElastiCache Redis, S3, and Terraform**.

---

## 🛠️ Phase 1: Prerequisites & Account Provisioning

To deploy this project live on AWS, you must have the following developer tools and accounts configured:

1. **Active AWS Account**: Full administrator permissions or IAM user with power user permissions.
2. **AWS CLI (v2)**: Installed locally on your development machine and configured with credentials:
   ```bash
   aws configure
   ```
3. **Terraform CLI**: Installed on your system (e.g. `brew install terraform` on macOS).
4. **Docker Engine**: Installed and running (required to compile the Django production image).
5. **Registered Domain & ACM SSL Certificate (Optional but highly recommended)**:
   * A custom domain registered under Route 53 (e.g. `api.quantum-mind.com`).
   * An SSL certificate provisioned via **AWS Certificate Manager (ACM)** in `us-east-1` for HTTPS routing.

---

## 🔑 Phase 2: Pre-Deployment AWS Asset Configurations

Before executing Terraform, the following base cloud assets must be manually initialized:

### 1. Terraform Backend S3 Bucket
Terraform stores state files securely in the cloud to enable teamwork and locking.
* Go to the S3 Console and create a bucket named: `quantum-mind-terraform-state` in region `us-east-1` (or match your selected region).

### 2. Create the Amazon ECR Container Registry
Create a private registry to host the compiled Docker production images:
* **Registry Name**: `quantum-mind`
* *Save the repository URI (e.g., `<account_id>.dkr.ecr.us-east-1.amazonaws.com/quantum-mind`).*

### 3. Create the Secrets Manager Production Vault
To prevent hardcoded credentials from leaking in git, the ECS container pulls configuration values directly from **AWS Secrets Manager** at runtime.
* Create a new Secret named: `quantum-mind-production-secrets`.
* Define the following Key-Value pairs inside:
  
  | Secret Key | Example Production Value / Description |
  | :--- | :--- |
  | `DJANGO_SECRET_KEY` | `secure-production-secret-key-32-chars` |
  | `DATABASE_URL` | `postgres://db_user:db_password@rds_endpoint:5432/quantum_mind` (Fill temporary value first, update with final RDS hostname post-Terraform apply) |
  | `REDIS_URL` | `redis://redis_endpoint:6379/0` (Fill temporary value first, update with ElastiCache endpoint post-Terraform apply) |
  | `ANTHROPIC_API_KEY` | `sk-ant-api03-xxxx...` (Your live Anthropic Claude key) |
  | `ELEVENLABS_API_KEY` | `your-eleven-labs-production-key` |
  | `AWS_ACCESS_KEY_ID` | `AKIAxxxxxxxxxxxx` (Required if uploading audios to S3 via backend client) |
  | `AWS_SECRET_ACCESS_KEY` | `xxxxxxx...` |

---

## 🚨 Critical Architecture Catch: The Missing Celery Worker

Reviewing [main.tf](file:///Users/alirehan/Desktop/quantum_mind/terraform/main.tf), the current setup registers the S3 bucket, RDS database, Redis, and the main Django **web server**, but **lacks configurations to run the Celery task worker in ECS**.

Without running Celery, async script and audio generation will fail completely in production.

### How to Fix This
Copy and paste this Celery Task and Service definition block directly at the end of your [terraform/main.tf](file:///Users/alirehan/Desktop/quantum_mind/terraform/main.tf) file. It reuses the exact same Docker image but launches with the Celery runtime command instead of Gunicorn.

```hcl
# ── Celery Fargate Task Definition ──────────────────────────────────────────
resource "aws_ecs_task_definition" "celery" {
  family                   = "${var.project_name}-celery"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.ecs_cpu
  memory                   = var.ecs_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "celery"
      image     = var.ecr_image_url
      essential = true
      command   = ["celery", "-A", "config", "worker", "--loglevel=info"]
      environment = [
        { name = "DJANGO_SETTINGS_MODULE", value = "config.settings.production" },
      ]
      secrets = [
        { name = "DJANGO_SECRET_KEY",    valueFrom = "${var.secrets_manager_arn}:DJANGO_SECRET_KEY::" },
        { name = "DATABASE_URL",         valueFrom = "${var.secrets_manager_arn}:DATABASE_URL::" },
        { name = "REDIS_URL",            valueFrom = "${var.secrets_manager_arn}:REDIS_URL::" },
        { name = "ANTHROPIC_API_KEY",    valueFrom = "${var.secrets_manager_arn}:ANTHROPIC_API_KEY::" },
        { name = "ELEVENLABS_API_KEY",   valueFrom = "${var.secrets_manager_arn}:ELEVENLABS_API_KEY::" },
        { name = "AWS_ACCESS_KEY_ID",    valueFrom = "${var.secrets_manager_arn}:AWS_ACCESS_KEY_ID::" },
        { name = "AWS_SECRET_ACCESS_KEY",valueFrom = "${var.secrets_manager_arn}:AWS_SECRET_ACCESS_KEY::" },
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/${var.project_name}"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "celery"
        }
      }
    }
  ])
}

# ── Celery Fargate ECS Service ──────────────────────────────────────────────
resource "aws_ecs_service" "celery" {
  name            = "${var.project_name}-celery"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.celery.arn
  desired_count   = 1 # Adjust scale depending on background processing load
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id # Celery is securely isolated in the private subnets
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = false
  }

  depends_on = [aws_elasticache_cluster.redis]
}
```

---

## 🚀 Phase 3: Infrastructure Deployment & Pipeline Commands

Follow these execution steps sequentially to push the setup live:

### 1. Initialize and Apply Terraform
Ensure you have created `terraform/terraform.tfvars` with the correct inputs:
```hcl
db_username         = "postgres"
db_password         = "YourSecureProductionPassword123!"
ecr_image_url       = "<your-account-id>.dkr.ecr.us-east-1.amazonaws.com/quantum-mind:latest"
secrets_manager_arn = "arn:aws:secretsmanager:us-east-1:<your-account-id>:secret:quantum-mind-production-secrets-xxxxxx"
```

Then execute:
```bash
cd terraform
terraform init
terraform plan
terraform apply
```
*Note down the outputs from Terraform, particularly the **RDS Endpoint** (`db_endpoint`) and **ElastiCache Address** (`redis_endpoint`).*

### 2. Update Secrets Manager Configurations
Go back to **AWS Secrets Manager**, select `quantum-mind-production-secrets`, and update the temporary variables with the real, live endpoints provisioned by Terraform:
* `DATABASE_URL` ➔ `postgres://postgres:<your_RDS_password>@<RDS_ENDPOINT>:5432/quantum_mind`
* `REDIS_URL` ➔ `redis://<ELASTICACHE_ENDPOINT>:6379/0`

### 3. Build & Ship the Container to AWS ECR
From your local terminal in the project root:
```bash
# 1. Login to AWS Elastic Container Registry
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <your-aws-account-id>.dkr.ecr.us-east-1.amazonaws.com

# 2. Build the production Docker image
docker build -f docker/Dockerfile -t quantum-mind .

# 3. Tag the image
docker tag quantum-mind:latest <your-aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/quantum-mind:latest

# 4. Push to ECR
docker push <your-aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/quantum-mind:latest
```

---

## 🏁 Phase 4: Database Migrations & Validation

Once the container image is live in ECR and Fargate containers are booting, run a one-time ECS task override to apply your database migrations securely to your RDS database instance:

```bash
aws ecs run-task \
  --cluster quantum-mind-cluster \
  --task-definition quantum-mind-web \
  --launch-type FARGATE \
  --network-configuration '{"awsvpcConfiguration":{"subnets":["subnet-xxxx","subnet-yyyy"],"securityGroups":["sg-zzzz"],"assignPublicIp":"ENABLED"}}' \
  --overrides '{"containerOverrides":[{"name":"web","command":["python","manage.py","migrate"]}]}'
```
*(Replace `subnet-xxxx`, `subnet-yyyy` and `sg-zzzz` with your public subnet IDs and ecs security group ID outputted by Terraform).*

Once the migrations complete successfully, your production Django container cluster is live, secure, connected to PostgreSQL, and completely operational!
