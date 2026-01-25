# Use AWS Lambda Python runtime
FROM public.ecr.aws/lambda/python:3.11

# Install system dependencies
RUN yum install -y \
    libsndfile \
    ffmpeg \
    && yum clean all

# Upgrade pip first
RUN pip install --upgrade pip

# Copy requirements
COPY requirements.txt ${LAMBDA_TASK_ROOT}/

# Install Python dependencies in stages for better caching
# Install numpy and scipy first (they're dependencies for others)
RUN pip install --no-cache-dir --timeout=300 numpy==1.24.3 scipy==1.11.4

# Install audio processing libraries
RUN pip install --no-cache-dir --timeout=300 librosa==0.10.1 soundfile==0.12.1

# Install MIDI libraries
RUN pip install --no-cache-dir --timeout=300 mido==1.3.2 pretty-midi==0.2.10

# Install basic-pitch (largest package)
RUN pip install --no-cache-dir --timeout=300 basic-pitch==0.3.2

# Install AWS SDK
RUN pip install --no-cache-dir boto3==1.34.34

# Copy function code
COPY handler.py ${LAMBDA_TASK_ROOT}/
COPY chord_utils.py ${LAMBDA_TASK_ROOT}/

# Set the CMD to your handler
CMD [ "handler.lambda_handler" ]
