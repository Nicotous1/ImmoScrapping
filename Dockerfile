FROM public.ecr.aws/lambda/python:3.8

WORKDIR /app

# Install Node.js and npm
RUN curl -fsSL https://rpm.nodesource.com/setup_18.x | bash - \
    && yum install -y nodejs

COPY ./README.rst /app/README.rst
COPY ./HISTORY.rst /app/HISTORY.rst
COPY ./setup.py /app/setup.py
RUN pip3 install .

COPY ./immo_scrap /app/immo_scrap
RUN pip3 install .

COPY ./aws/aws_lambda.py ${LAMBDA_TASK_ROOT}

CMD [ "aws_lambda.lambda_handler" ] 