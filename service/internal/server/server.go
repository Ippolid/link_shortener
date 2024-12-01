package server

import (
	"net/http"
	"service/internal/database"

	"github.com/gin-contrib/gzip"
	"github.com/gin-gonic/gin"
)

type Server struct {
	host     string
	database *database.DataBase
}

func New(host string, st *database.DataBase) *Server {
	s := &Server{
		host:     host,
		database: st,
	}

	return s
}

func (s *Server) newAPI() *gin.Engine {
	engine := gin.New()

	engine.Use(gzip.Gzip(gzip.BestSpeed))
	engine.RunTLS(":8090", "server.crt", "server.key")

	engine.GET("/health", func(ctx *gin.Context) {
		ctx.Status(http.StatusOK)
	})

	engine.POST("/url", s.HandlerСreateUrl)
	engine.GET("/:url", s.HandlerTransferToOriginalLink)
	engine.DELETE("/:user/delete/:shorturl", s.HandlerDeleteLink)
	engine.PUT("/:user/change/:shorturl/:time", s.HandlerEditLink)
	engine.GET("/statistic/:user", s.GetLinks)
	engine.GET("/statistic/:user/:shorturl", s.GetLinkStatistic)

	return engine
}

func (s *Server) Start() {
	s.newAPI().Run(s.host)
}
