cd ..;
docker build -t immo_scrap:latest . ;
docker tag immo_scrap:latest 274199371873.dkr.ecr.eu-west-3.amazonaws.com/immo_scrap:latest ;
docker push 274199371873.dkr.ecr.eu-west-3.amazonaws.com/immo_scrap:latest ;
