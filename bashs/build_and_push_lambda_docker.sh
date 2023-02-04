cd ..;

docker login -u AWS -p $(aws ecr get-login-password --region eu-west-3) 274199371873.dkr.ecr.eu-west-3.amazonaws.com;
aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws;

docker build -t immo_scrap:latest . ;
docker tag immo_scrap:latest 274199371873.dkr.ecr.eu-west-3.amazonaws.com/immo_scrap:latest ;
docker push 274199371873.dkr.ecr.eu-west-3.amazonaws.com/immo_scrap:latest ;
