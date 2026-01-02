FROM python:3.14-slim

WORKDIR /app

COPY ./app /app

RUN pip install --no-cache-dir -r requirements.txt

## Handy dev tools
RUN apt-get update && apt-get install -y curl vim jq && \
    mkdir -p /etc/skel   && \
    printf 'PS1="\033[1;32m\u@zeta-mcp:\w/$\033[0m "\nalias ls="ls --color=auto"\nalias vi=vim\n' >> /etc/skel/.bashrc && \
        printf "syntax on\n:set hlsearch\n:set ruler\n:set ts=2\n:set list\n:set listchars=tab:<>\ninoremap jj <ESC>" >> /etc/skel/.vimrc && \
    cp /etc/skel/.bashrc /root/  && \
    cp /etc/skel/.vimrc  /root/

EXPOSE 8001

CMD ["fastmcp", "run", "server.py", "--transport", "sse", "--host", "0.0.0.0", "--port", "8001"]
