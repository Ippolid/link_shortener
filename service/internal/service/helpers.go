package service

import (
	"crypto/sha1"
	"encoding/hex"
	"fmt"
	"os"
	"service/internal/database"
	"strconv"
	"time"
)

func GenerateShortURL(userid int, url string) string {
	hash := sha1.New()
	url1 := url + strconv.Itoa(userid)
	hash.Write([]byte(url1))
	return hex.EncodeToString(hash.Sum(nil))[:8]
}

func NewLink(userId int, oldlink string) string {
	domen := os.Getenv("DOMEN")
	indeficator := GenerateShortURL(userId, oldlink)
	return domen + indeficator
}

func DeleteOverdueLines(closeChan chan struct{}, n time.Duration, database *database.DataBase) {
	for {
		select {
		case <-closeChan:
			return
		case <-time.After(n):
			timenow := int(time.Now().Unix())
			err := database.DeleteBytime(timenow)
			if err != nil {
				fmt.Printf("ERR0R %v", err)
			}
		}
	}
}
