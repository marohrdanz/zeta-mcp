FROM node:22.4.1-bookworm-slim

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install
COPY . .
EXPOSE 3001
ENV PORT=3001

RUN apt-get update && apt-get install -y curl vim jq && \
    npm install && \
    mkdir -p /etc/skel   && \
    printf 'PS1="\033[1;32m\u@mcp-frontend:\w/$\033[0m "\nalias ls="ls --color=auto"\nalias vi=vim\n' >> /etc/skel/.bashrc && \
        printf "syntax on\n:set hlsearch\n:set ruler\n:set ts=2\n:set list\n:set listchars=tab:<>\ninoremap jj <ESC>" >> /etc/skel/.vimrc && \
    cp /etc/skel/.bashrc /root/  && \
    cp /etc/skel/.vimrc  /root/

CMD ["npm", "start"]
