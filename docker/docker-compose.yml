version: '3'
services:
  ts:
    image: "trackstudio-report:latest"
    restart: always
    ports:
      - 5000:5000
    volumes:
      - ./config.py:/src/config.py
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "10"
