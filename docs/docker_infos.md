# Build docker image

docker build -t immo_scrap .

# Run with compose

docker-compose up

# Run interatively

docker run -it immo_scrap bash

# build

docker build -t immo_scrap:latest .

# Export to AWS ECR PRIVATE

## CREATE A PRIVATE REPO

aws ecr create-repository --repository-name immo_scrap --region eu-west-3

## Login to private repo

docker login -u AWS -p $(aws ecr get-login-password --region eu-west-3) 274199371873.dkr.ecr.eu-west-3.amazonaws.com

## Export to private repo

docker tag immo_scrap:latest 274199371873.dkr.ecr.eu-west-3.amazonaws.com/immo_scrap:latest
docker push 274199371873.dkr.ecr.eu-west-3.amazonaws.com/immo_scrap:latest

# Export to AWS ECR PPUBLIC

aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws
docker login -u AWS -p $(aws ecr get-login-password --region us-east-1) public.ecr.aws/s7u9x5w7/immo_scrap
docker tag immo_scrap public.ecr.aws/s7u9x5w7/immo_scrap
docker push public.ecr.aws/s7u9x5w7/immo_scrap
