# ERP-WMS 前端镜像（构建产物由 Nginx 托管）
FROM node:20-alpine AS build

WORKDIR /app

# 先复制依赖清单安装依赖，利用层缓存
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# 运行阶段：Nginx 托管静态文件，并反向代理 /api 到后端
FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
