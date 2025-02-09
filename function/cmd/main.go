package main

import (
	"fmt"
	"net/http"
	"os"

	server "manabiya.ai/function"

	// Blank-import the function package so the init() runs
	"github.com/gorilla/mux"
	_ "manabiya.ai/function"
)

func main() {
	// ルーターを作成
	r := mux.NewRouter()

	// URIごとにハンドラを登録
	r.PathPrefix("/").HandlerFunc(server.Main)

	service_port := os.Getenv("SERVICE_PORT")

	// サーバーを起動
	fmt.Println("Starting server on :" + service_port)
	if err := http.ListenAndServe(":"+service_port, r); err != nil {
		fmt.Println("Error starting server:", err)
	}
}
