# Use AWS Lambda Python runtime
FROM public.ecr.aws/lambda/python:3.11

# Install system dependencies
RUN yum install -y \
    libsndfile \
    ffmpeg \
    && yum clean all

# Copy requirements
COPY requirements.txt ${LAMBDA_TASK_ROOT}/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy function code
COPY handler.py ${LAMBDA_TASK_ROOT}/
COPY chord_utils.py ${LAMBDA_TASK_ROOT}/

# Set the CMD to your handler
CMD [ "handler.lambda_handler" ]
