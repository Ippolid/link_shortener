# Первая стадия: сборка приложения
FROM golang:1.23.3 AS builder

# Устанавливаем рабочую директорию для сборки
WORKDIR /app

# Копируем файлы зависимостей
COPY ./service/go.mod ./service/go.sum ./ 
# Устанавливаем зависимости
RUN go mod download

# Копируем весь исходный код проекта
COPY ../service ./
# Собираем исполняемый файл
RUN go build -o /app/service1 ./cmd/main.go

# Вторая стадия: минимальный образ для запуска
FROM ubuntu:22.04

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем скомпилированный бинарный файл из первой стадии
COPY --from=builder /app/service1 /app/service1

# Указываем команду для запуска приложения
CMD ["./service1"]
