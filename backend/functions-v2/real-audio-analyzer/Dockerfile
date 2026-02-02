# Dockerfile for Real Audio Analysis Lambda
# Uses Python with audio analysis libraries

FROM public.ecr.aws/lambda/python:3.9

# Install system dependencies for audio processing
RUN yum update -y && \
    yum install -y \
    gcc \
    gcc-c++ \
    make \
    cmake \
    pkgconfig \
    libsndfile-devel \
    ffmpeg \
    && yum clean all

# Copy requirements and install Python dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install --no-cache-dir -r requirements.txt

# Copy function code
COPY real_audio_analyzer.py ${LAMBDA_TASK_ROOT}
COPY lambda_function.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler
CMD ["lambda_function.lambda_handler"]