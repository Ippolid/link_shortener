package server

import "time"

type RequestCreateLink struct {
	OldurL string `json:"oldurl" binding:"required"`
	UserID string `json:"userid" binding:"required"`
}

// Структура для ответа
type ResponseCreateLinkBody struct {
	ShortURL string `json:"shorturl"`
}

type ResponseGetLinks struct {
	Links map[string]string `json:"links"`
}

type ResponseLinkStatistic struct {
	ExpireTime    time.Time `json:"expiretime"`
	TransferCount int       `json:"transferCount"`
	OrigLink      string    `json:"link"`
}
