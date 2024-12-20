FROM public.ecr.aws/lambda/python:3.8

WORKDIR /app

RUN apt install nodejs -y

COPY ./README.rst /app/README.rst
COPY ./HISTORY.rst /app/HISTORY.rst
COPY ./setup.py /app/setup.py
RUN pip3 install .

COPY ./immo_scrap /app/immo_scrap
RUN pip3 install .

COPY ./aws/aws_lambda.py ${LAMBDA_TASK_ROOT}

CMD [ "aws_lambda.lambda_handler" ] 