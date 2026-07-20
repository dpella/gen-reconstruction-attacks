FROM python:3.12.3

RUN mkdir /app
WORKDIR /app

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  ca-certificates \
  curl \
  wget \
  git \
  build-essential \
  glpk-utils \
  && apt-get clean -y

RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

##
# Latex
##
RUN apt-get update

RUN apt-get update \
	&& \
    apt-get install -y \
	texlive-xetex \
	zathura \
	latexmk \
	texlive-luatex \
	texlive-science \
	texlive-extra-utils \
	texlive-bibtex-extra \
	python3-pygments \
	biber \
	texlive-fonts-extra \
	chktex