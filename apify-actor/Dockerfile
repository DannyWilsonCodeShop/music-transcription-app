FROM apify/actor-node:20

COPY package*.json ./

RUN npm install --production

COPY . ./

CMD npm start
