FROM nginx:stable-alpine
LABEL maintainer="kkt"

USER root

COPY uwsgi_params /etc/nginx/uwsgi_params
COPY nginx.conf /etc/nginx/nginx.conf
COPY shapi.nginx.conf /etc/nginx/sites-available/shapi.nginx.conf

RUN mkdir /etc/nginx/sites-enabled
RUN ln -s /etc/nginx/sites-available/shapi.nginx.conf /etc/nginx/sites-enabled/

CMD ["nginx", "-g", "daemon off;"]