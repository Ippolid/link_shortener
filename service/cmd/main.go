package main

import (
	"database/sql"
	"log"
	"service/internal/database"
	"service/internal/server"
	"service/internal/service"
	"time"

	_ "github.com/lib/pq"
)

func main() {
	postgresURI := "postgres://postgres:1234@localhost:5432"
	db, err := sql.Open("postgres", postgresURI)
	if err != nil {
		log.Fatal("open", err)
	}

	datab, err := database.NewDataBase(db)
	if err != nil {
		log.Fatal("open", err)
	}
	defer db.Close()

	if err := db.Ping(); err != nil {
		log.Fatal("ping", err)
	}

	// datab.InsertLink(2, "https://vk.com/audios301631204", service.NewLink(2, "https://vk.com/audios301631204"))
	// datab.InsertLink(2, "https://vk.com/audios3016312041", service.NewLink(2, "https://vk.com/audios301631204111111"))
	// datab.InsertLink(3, "https://vk.com/audios3016312041", service.NewLink(3, "https://vk.com/audios3016312041"))
	// datab.InsertLink(3, "https://vk.com/audios3016312041", service.NewLink(3, "https://vk.com/audios3016312041"))
	// datab.InsertLink(2, "https://vk.com/audios30162041", service.NewLink(2, "https://vk.com/audios30163204"))

	// datab.DeleteLink(2, service.NewLink(2, "https://vk.com/audios301631204111111"))

	// datab.EditExpiretime(3, service.NewLink(3, "https://vk.com/audios301631204"), 24)

	// z, _ := datab.GetLinkbyShortlink(service.NewLink(3, "https://vk.com/audios301631204"))

	// fmt.Println(z)

	// p, _ := datab.GetUserBylink(service.NewLink(2, "https://vk.com/audios30163204"))
	// fmt.Println(p)

	// k, _ := datab.GetUseridslinks(2)
	// fmt.Println(k)

	// k, err := datab.GetLinkbyShortlink("0b95c551")
	// datab.GetLinkbyShortlink("0b95c551")
	// datab.GetLinkbyShortlink("0b95c551")
	// fmt.Println(k)
	// fmt.Println(err)
	closeChan := make(chan struct{})
	time := time.Hour * 1
	go service.DeleteOverdueLines(closeChan, time, datab)
	server := server.New(":8090", datab)
	server.Start()
	close(closeChan)

}
