package main

import (
	"fmt"
	server "gc-hackathon.ai/function"
	"net/http"

	// Blank-import the function package so the init() runs
	_ "gc-hackathon.ai/function"
	"github.com/gorilla/mux"
)

func main() {
	// ルーターを作成
	r := mux.NewRouter()

	// URIごとにハンドラを登録
	r.PathPrefix("/").HandlerFunc(server.Main)

	// サーバーを起動
	fmt.Println("Starting server on :3002")
	if err := http.ListenAndServe(":3002", r); err != nil {
		fmt.Println("Error starting server:", err)
	}
}
