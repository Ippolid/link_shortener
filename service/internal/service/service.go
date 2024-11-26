package service

import "service/internal/database"

func CreateLink(userid int64, link string, r *database.Storage) error {
	p := NewLink(link)
	r.AppendElem(userid, link, p, 0)
	return nil
}
