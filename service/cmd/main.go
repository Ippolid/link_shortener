package main

import (
	"database/sql"
	"log"
	"time"

	_ "github.com/lib/pq"
)

const (
	queryCreateUsersTable = `CREATE TABLE IF NOT EXISTS users (
		id bigserial PRIMARY KEY,
		name text NOT NULL,
		password text NOT NULL
	)`

	queryGetUser    = `SELECT * FROM users WHERE id = $1`
	queryCreateUser = `INSERT INTO users (name, password) VALUES ($1, $2) RETURNING id`
)

func main() {
	// sk, _ := database.NewStorage()
	// service.CreateLink(1, "https://habr.com/ru/companies/inDrive/articles/690088/", &sk)
	// fmt.Println(sk)
	postgresURI := "postgres://postgres:password@localhost:5432"
	db, err := sql.Open("postgres", postgresURI)
	if err != nil {
		log.Fatal("open", err)
	}

	defer db.Close()

	if err := db.Ping(); err != nil {
		log.Fatal("ping", err)
	}

	_, err = db.Exec(queryCreateUsersTable)
	if err != nil {
		log.Fatal(err)
	}
	time.Sleep(1000 * time.Second)
}
