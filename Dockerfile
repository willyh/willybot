FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN apt update \
        && apt install libportaudio2 libportaudiocpp0 portaudio19-dev libasound-dev libsndfile1-dev swig libpulse-dev -y
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./listen.py" ]
