FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

ARG VITE_API_BASE_URL=
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ARG VITE_ENABLE_DEV_LOGIN=false
ENV VITE_ENABLE_DEV_LOGIN=$VITE_ENABLE_DEV_LOGIN

RUN npm run build

FROM node:20-alpine

WORKDIR /app
RUN npm install -g serve@14
COPY --from=build /app/dist ./dist

ENV PORT=5173
EXPOSE 5173

CMD sh -c "serve -s dist -l ${PORT:-5173}"
