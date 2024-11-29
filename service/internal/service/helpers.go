package service

import (
	"crypto/sha1"
	"encoding/hex"
	"strconv"
)

const domen string = "http://loclahost:8090/"

func GenerateShortURL(userid int, url string) string {
	hash := sha1.New()
	url1 := url + strconv.Itoa(userid)
	hash.Write([]byte(url1))
	return hex.EncodeToString(hash.Sum(nil))[:8]
}

func NewLink(userId int, oldlink string) string {
	indeficator := GenerateShortURL(userId, oldlink)
	return domen + indeficator
}
