FROM iwatkot/blender:latest

ARG API_TOKEN
ENV API_TOKEN=${API_TOKEN}
ARG STATS_HOST
ENV STATS_HOST=${STATS_HOST}

# Clone external repo and copy data/docs
RUN git clone --depth 1 https://github.com/iwatkot/maps4fs.git /tmp/maps4fs \
    && cp -r /tmp/maps4fs/docs /usr/src/app/docs \
    && rm -rf /tmp/maps4fs

RUN git clone --depth 1 https://github.com/iwatkot/maps4fsdata.git /tmp/maps4fsdata \
    && cd /tmp/maps4fsdata \
    && chmod +x prepare_data.sh \
    && ./prepare_data.sh \
    && cp -r data /usr/src/app/templates \
    && rm -rf /tmp/maps4fsdata

COPY requirements.txt /usr/src/app/requirements.txt
COPY entrypoint.sh /usr/src/app/entrypoint.sh
RUN chmod +x /usr/src/app/entrypoint.sh

# Ensure that we're using osmnx installed from fork, not the main pypi version.
RUN pip install git+https://github.com/iwatkot/osmnx.git
RUN pip install -r requirements.txt

EXPOSE 8000

ENV PYTHONPATH .:${PYTHONPATH}
CMD ["/usr/src/app/entrypoint.sh"]
