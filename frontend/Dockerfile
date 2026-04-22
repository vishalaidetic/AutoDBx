FROM node:18-slim

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Build step if needed, but for dev we can just run vite
# RUN npm run build

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
