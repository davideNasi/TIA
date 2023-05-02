FROM nvidia/cuda:11.1.1-devel-ubuntu16.04
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y
RUN apt-get install -y build-essential \
checkinstall \
libreadline-gplv2-dev \
libncursesw5-dev \
libssl-dev \
libsqlite3-dev \
tk-dev \
libgdbm-dev \
libc6-dev \
libbz2-dev \
zlib1g-dev \
openssl \
libffi-dev \
python3-dev \
python3-setuptools \
libjpeg-dev \
zlib1g-dev \
lzma \
liblzma-dev \
wget -y

# Python 3.7
RUN mkdir /tmp/Python37
WORKDIR /tmp/Python37
RUN wget https://www.python.org/ftp/python/3.7.0/Python-3.7.0.tar.xz
RUN tar xvf Python-3.7.0.tar.xz
WORKDIR /tmp/Python37/Python-3.7.0
RUN ./configure
RUN make altinstall

# Dependencies
RUN pip3.7 install --upgrade pip
RUN pip3.7 install torch==1.8.0+cu111 torchvision==0.9.0+cu111 torchaudio==0.8.0 -f https://download.pytorch.org/whl/torch_stable.html
RUN pip3.7 install "pillow<7"
RUN pip3.7 install easydict pyyaml==5.4.1 opencv-python scipy

# TIA
RUN apt install git -y
WORKDIR /
ARG CACHEBUST=7
RUN git clone https://github.com/davideNasi/TIA.git
WORKDIR /TIA
CMD ["scripts/wolves/train.sh"]

