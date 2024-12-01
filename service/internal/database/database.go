package database

import (
	"database/sql"
	"fmt"
	"time"

	_ "github.com/lib/pq"
)

type DataBase struct {
	db *sql.DB
}

// NewDBWrapper — конструктор для обёртки
func NewDataBase(db *sql.DB) (*DataBase, error) {
	_, err := db.Exec(queryCreateLinksTable)
	if err != nil {
		return nil, err
	}
	return &DataBase{db: db}, nil
}

const (
	queryCreateLinksTable = `CREATE TABLE IF NOT EXISTS links (
		id bigserial PRIMARY KEY,
		userId integer NOT NULL,
		oldLink text NOT NULL,
		shortLink text NOT NULL UNIQUE,
		expireTime integer NOT NULL,
		transfercounter integer NOT NULL
	)`

	queryInsertLink = `
		INSERT INTO links (userId, oldLink, shortLink, expireTime,transfercounter)
		VALUES ($1, $2, $3, $4,0)
		ON CONFLICT (shortLink) DO NOTHING;`

	queryGetLinks = `SELECT shortLink FROM links WHERE userId = $1;`

	queryDelete = `
		DELETE FROM links
		WHERE shortLink = $1;
	`
	queryGetUser = `SELECT userId
		FROM links
		WHERE shortLink = $1;`

	queryEditExpire = `
		UPDATE links
		SET expireTime = $1
		WHERE shortLink = $2;
	`
	postgresURI = "postgres://postgres:password@localhost:5432"

	queryGetLinkbyShort  = `SELECT oldLink FROM links WHERE shortLink = $1;`
	queryTransfercounter = `
		UPDATE links
		SET transfercounter = transfercounter + 1
		WHERE shortLink = $1;
	`

	queryGetStatic = `SELECT expireTime, transfercounter FROM links WHERE shortLink = $1;`
)

func (base *DataBase) InsertLink(userId int, oldLink, shortLink string) error {
	expireTime := int((time.Now().Add(time.Hour * 744)).Unix())
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

func (base *DataBase) GetUserBylink(shortlink string) (int, error) {
	var userId int

	err := base.db.QueryRow(queryGetUser, shortlink).Scan(&userId)
	if err == sql.ErrNoRows {
		return 0, fmt.Errorf("no user found for shortLink: %s", shortlink)
	} else if err != nil {
		return 0, fmt.Errorf("error executing query: %v", err)
	}

	return userId, nil
}

func (base *DataBase) DeleteLink(userId int, shortlink string) error {
	linkowner, err := base.GetUserBylink(shortlink)
	if err != nil {
		return fmt.Errorf("error for geting owner of links: %s", shortlink)
	}
	if linkowner == userId {
		_, err := base.db.Exec(queryDelete, shortlink)
		if err != nil {
			return fmt.Errorf("error deleting by shortLink: %v", err)
		}
	}
	return nil
}

func (base *DataBase) EditExpiretime(userId int, shortlink string, hours int) error {
	linkowner, err := base.GetUserBylink(shortlink)
	if err != nil {
		return fmt.Errorf("error for geting owner of links: %s", shortlink)
	}
	if linkowner == userId {
		expireTime := int((time.Now().Add(time.Hour * time.Duration(hours))).Unix())
		_, err := base.db.Exec(queryEditExpire, expireTime, shortlink)
		if err != nil {
			return fmt.Errorf("error updating expireTime: %v", err)
		}
	}
	return nil
}

func (base *DataBase) GetLinkbyShortlink(shortLink string) (string, error) {
	var oldLink string

	err := base.db.QueryRow(queryGetLinkbyShort, shortLink).Scan(&oldLink)
	if err == sql.ErrNoRows {
		return "", fmt.Errorf("no oldLink found for shortLink: %s", shortLink)
	} else if err != nil {
		return "", fmt.Errorf("error executing query: %v", err)
	}
	go base.EditTransferCount(shortLink)
	return oldLink, nil
}

func (base *DataBase) EditTransferCount(shortLink string) error {
	_, err := base.db.Exec(queryTransfercounter, shortLink)
	if err != nil {
		return fmt.Errorf("error updating transfercounter: %w", err)
	}
	return nil
}

func (base *DataBase) GetLinkStatic(userId int, shortLink string) (int, int, error) {
	var expireTime int
	var transferCounter int

	linkowner, err := base.GetUserBylink(shortLink)
	if err != nil {
		return 0, 0, fmt.Errorf("error for geting owner of links: %s", shortLink)
	}
	if linkowner == userId {
		err := base.db.QueryRow(queryGetStatic, shortLink).Scan(&expireTime, &transferCounter)
		if err != nil {
			if err == sql.ErrNoRows {
				return 0, 0, fmt.Errorf("no record found for shortLink: %s", shortLink)
			}
			return 0, 0, err
		}
	}
	return expireTime, transferCounter, nil
}
