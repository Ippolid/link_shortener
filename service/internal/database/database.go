package database

import (
	"database/sql"
	"fmt"

	_ "github.com/lib/pq"
)

type DataBase struct {
	db *sql.DB
}

// NewDBWrapper — конструктор для обёртки
func NewDataBase(db *sql.DB) *DataBase {
	return &DataBase{db: db}
}

const (
	queryCreateLinksTable = `CREATE TABLE IF NOT EXISTS links (
		id bigserial PRIMARY KEY,
		userId integer NOT NULL,
		oldLink text NOT NULL,
		shortLink text NOT NULL UNIQUE,
		expireTime integer NOT NULL
	)`

	queryInsertLink = `
		INSERT INTO links1 (userId, oldLink, shortLink, expireTime)
		VALUES ($1, $2, $3, $4)
		ON CONFLICT (shortLink) DO NOTHING;`

	queryGetLinks = `SELECT shortLink FROM links WHERE userId = $1;`

	postgresURI = "postgres://postgres:password@localhost:5432"
)

func (base *DataBase) InsertLink(userId int, oldLink, shortLink string, expireTime int) error {

	_, err := base.db.Exec(queryInsertLink, userId, oldLink, shortLink, expireTime)

	if err != nil {
		return fmt.Errorf("error executing query: %v", err)
	}
	return nil
}

func (base *DataBase) GetUseridslinks(userId int) ([]string, error) {

	rows, err := base.db.Query(queryGetLinks, userId)
	if err != nil {
		return nil, fmt.Errorf("error executing query: %v", err)
	}
	defer rows.Close()

	var shortLinks []string
	for rows.Next() {
		var shortLink string
		if err := rows.Scan(&shortLink); err != nil {
			return nil, fmt.Errorf("error scanning row: %v", err)
		}
		shortLinks = append(shortLinks, shortLink)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error with rows: %v", err)
	}

	return shortLinks, nil
}
