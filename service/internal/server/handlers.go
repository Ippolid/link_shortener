package server

import (
	"encoding/json"
	"net/http"
	"service/internal/service"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
)

func (s *Server) HandlerСreateUrl(ctx *gin.Context) {

	var reqBody RequestCreateLink
	if err := json.NewDecoder(ctx.Request.Body).Decode(&reqBody); err != nil {
		ctx.AbortWithStatusJSON(http.StatusInternalServerError, err.Error())
		return
	}
	userid, err := strconv.Atoi(reqBody.UserID)
	if err != nil {
		ctx.AbortWithStatusJSON(http.StatusInternalServerError, err.Error())
		return
	}
	// Генерация короткого URL
	shortURL := service.NewLink(userid, reqBody.OldurL)

	shortlink := service.GenerateShortURL(userid, reqBody.OldurL)
	err1 := s.database.InsertLink(userid, reqBody.OldurL, shortlink)
	if err1 != nil {
		ctx.AbortWithStatusJSON(http.StatusInternalServerError, err1.Error())
		return
	}

	// Отправка ответа
	ctx.JSON(http.StatusOK, ResponseCreateLinkBody{
		ShortURL: shortURL,
	})

}

func (s *Server) HandlerTransferToOriginalLink(ctx *gin.Context) {
	shorturl := ctx.Param("url")

	link, err := s.database.GetLinkbyShortlink(shorturl)

	if err != nil {
		ctx.AbortWithStatusJSON(http.StatusInternalServerError, err.Error())
		return
	}
	ctx.Header("Content-Type", "text/plain")

	// Выполняем перенаправление (301 Redirect)
	ctx.Redirect(http.StatusMovedPermanently, link)

}

func (s *Server) HandlerDeleteLink(ctx *gin.Context) {
	user, err := strconv.Atoi(ctx.Param("user"))
	if err != nil {
		ctx.AbortWithStatusJSON(http.StatusInternalServerError, err.Error())
		return
	}
	shorturl := ctx.Param("shorturl")

	err = s.database.DeleteLink(user, shorturl)

	if err != nil {
		ctx.AbortWithStatusJSON(http.StatusInternalServerError, err.Error())
		return
	}

	ctx.Status(http.StatusOK)
}

func (s *Server) HandlerEditLink(ctx *gin.Context) {
	user, err := strconv.Atoi(ctx.Param("user"))
	if err != nil {
		ctx.AbortWithStatusJSON(http.StatusInternalServerError, err.Error())
		return
	}
	shorturl := ctx.Param("shorturl")

	time, err := strconv.Atoi(ctx.Param("time"))
	if err != nil {
		ctx.AbortWithStatusJSON(http.StatusInternalServerError, err.Error())
		return
	}

	err = s.database.EditExpiretime(user, shorturl, time)

	if err != nil {
		ctx.AbortWithStatusJSON(http.StatusInternalServerError, err.Error())
		return
	}

	ctx.Status(http.StatusOK)
}

func (s *Server) GetLinks(ctx *gin.Context) {
	user, err := strconv.Atoi(ctx.Param("user"))
	if err != nil {
		ctx.AbortWithStatusJSON(http.StatusInternalServerError, err.Error())
		return
	}

	links, err1 := s.database.GetUseridslinks(user)
	if err1 != nil {
		ctx.AbortWithStatusJSON(http.StatusInternalServerError, err1.Error())
		return
	}

	ctx.JSON(http.StatusOK, ResponseGetLinks{
		Links: links,
	})
}

func (s *Server) GetLinkStatistic(ctx *gin.Context) {
	user, err := strconv.Atoi(ctx.Param("user"))
	if err != nil {
		ctx.AbortWithStatusJSON(http.StatusInternalServerError, err.Error())
		return
	}
	shortlink := ctx.Param("shorturl")

	times, transfers, err1 := s.database.GetLinkStatic(user, shortlink)
	if err1 != nil {
		ctx.AbortWithStatusJSON(http.StatusInternalServerError, err1.Error())
		return
	}

	time1 := time.Unix(int64(times), 0)

	ctx.JSON(http.StatusOK, ResponseLinkStatistic{
		ExpireTime:    time1,
		TransferCount: transfers,
	})
}

// func (s *Server) handlerGet(ctx *gin.Context) {
// 	key := ctx.Param("key")

// 	v := s.storage.Get(key)
// 	if v == nil {
// 		ctx.AbortWithStatus(http.StatusBadRequest)
// 		return
// 	}

// 	ctx.JSON(http.StatusOK, Entry{Value: *v})

// }
