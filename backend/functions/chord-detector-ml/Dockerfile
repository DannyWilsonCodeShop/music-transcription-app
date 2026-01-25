# Use AWS Lambda Python runtime
FROM public.ecr.aws/lambda/python:3.11

# Install system dependencies
RUN yum install -y \
    libsndfile \
    ffmpeg \
    && yum clean all

# Upgrade pip and install wheel
RUN pip install --upgrade pip wheel

# Copy requirements
COPY requirements.txt ${LAMBDA_TASK_ROOT}/

# Install all dependencies at once with optimizations
# Use --prefer-binary to download pre-built wheels when available
# Increase timeout significantly for large packages
RUN pip install --no-cache-dir \
    --prefer-binary \
    --timeout=600 \
    --retries=10 \
    -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy function code
COPY handler.py ${LAMBDA_TASK_ROOT}/
COPY chord_utils.py ${LAMBDA_TASK_ROOT}/

# Set the CMD to your handler
CMD [ "handler.lambda_handler" ]
