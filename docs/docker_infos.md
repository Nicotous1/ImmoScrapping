# Build docker image

docker build -t immo_scrap .

# Run with compose

docker-compose up

# Run interatively

docker run -it immo_scrap bash

# Export to AWS ECR

aws ecr create-repository --repository-name immo_scrap --region eu-west-3
docker tag immo_scrap 274199371873.dkr.ecr.eu-west-3.amazonaws.com/immo_scrap

docker login -u AWS -p $(aws ecr get-login-password --region eu-west-3) 274199371873.dkr.ecr.eu-west-3.amazonaws.com
docker push 274199371873.dkr.ecr.eu-west-3.amazonaws.com/immo_scrap

aws ecr-public get-login-password --region eu-west-3 | docker login --username AWS --password-stdin public.ecr.aws
docker login -u AWS -p $(aws ecr get-login-password --region us-east-1) public.ecr.aws/s7u9x5w7/immo_scrap

docker tag immo_scrap public.ecr.aws/s7u9x5w7/immo_scrap
docker push public.ecr.aws/s7u9x5w7/immo_scrap
