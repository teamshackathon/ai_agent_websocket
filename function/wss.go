package main

import (
	"cloud.google.com/go/speech/apiv1"
	"cloud.google.com/go/vertexai/genai"
	"context"
	"encoding/base64"
	"fmt"
	socketio "github.com/googollee/go-socket.io"
	"github.com/googollee/go-socket.io/engineio"
	"github.com/googollee/go-socket.io/engineio/transport"
	"github.com/googollee/go-socket.io/engineio/transport/polling"
	"github.com/googollee/go-socket.io/engineio/transport/websocket"
	speechpb "google.golang.org/genproto/googleapis/cloud/speech/v1"
	"log"
	"net/http"
	"os"
	"strings"
	"sync"
)

// グローバルクライアント
var (
	speechClient *speech.Client
	genaiClient  *genai.Client
	speechOnce   sync.Once
	genaihOnce   sync.Once
)

func getSpeechClient() (*speech.Client, error) {
	var err error
	speechOnce.Do(func() {
		ctx := context.Background()
		speechClient, err = speech.NewClient(ctx)
	})
	return speechClient, err
}

func getGeminiClient() (*genai.Client, error) {
	var err error
	genaihOnce.Do(func() {
		location := "asia-northeast1"

		ctx := context.Background()
		genaiClient, err = genai.NewClient(ctx, os.Getenv("GCP_PROJECT"), location)
	})
	return genaiClient, err
}

// Easier to get running with CORS. Thanks for help @Vindexus and @erkie
var allowOriginFunc = func(r *http.Request) bool {
	origin := r.Header.Get("Origin")
	coses := strings.Split(os.Getenv("COSE_ORIGIN"), ",")
	for _, v := range coses {
		// 特定のオリジンのみ許可
		if origin == v {
			return true
		}
	}
	return false
}

func main() {
	log.SetFlags(0)

	// Socket.IOサーバーの作成
	server := socketio.NewServer(&engineio.Options{
		Transports: []transport.Transport{
			&polling.Transport{
				CheckOrigin: allowOriginFunc,
			},
			&websocket.Transport{
				CheckOrigin: allowOriginFunc,
			},
		},
	})

	// イベントハンドラの設定
	server.OnConnect("/", func(s socketio.Conn) error {
		s.SetContext("")
		log.Println("Client connected:", s.ID())
		return nil
	})

	// メッセージを受け取るイベント
	server.OnEvent("/", "message", func(s socketio.Conn, msg string) {
		log.Println("Received message:", msg)
	})

	// メッセージを受け取るイベント
	server.OnEvent("/", "audio_data", func(s socketio.Conn, audioData []byte) {
		log.Println("Received audio data.")
		decodedAudioData, err := base64.StdEncoding.DecodeString(string(audioData))
		if err != nil {
			log.Println("Error decoding base64 audio data:", err)
			return
		}

		transcribedText, err := processAudioWithAI(decodedAudioData)
		if err != nil {
			log.Println("Error processing audio:", err)
			return
		}
		log.Println("Transcribed text:", transcribedText)
	})

	// クライアントが切断したときの処理
	server.OnDisconnect("/", func(s socketio.Conn, reason string) {
		log.Println("Client disconnected:", s.ID(), reason)
	})

	// HTTPサーバーの作成とSocket.IOサーバーのハンドリング
	http.Handle("/socket.io/", server)
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		// デフォルトのHTMLファイルを返す
		http.ServeFile(w, r, "index.html")
	})

	// サーバーの起動（Cloud Runの場合はポート3002を利用）
	port := os.Getenv("SERVICE_PORT")
	log.Println("Starting WebSocket server on :" + port)
	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatal(err)
	}
}

func setResponseHeaders(w http.ResponseWriter, r *http.Request) {
	origin := r.Header.Get("Origin")
	coses := strings.Split(os.Getenv("COSE_ORIGIN"), ",")
	for _, v := range coses {
		// 特定のオリジンのみ許可
		if origin == v {
			w.Header().Set("Access-Control-Allow-Origin", origin)
			break
		}
	}

	w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
}

func processAudioWithAI(audioData []byte) (string, error) {

	if len(audioData) < 1000 { // 例: データが小さい場合
		log.Println("Skipping small audio fragment")
		return "", nil
	}
	log.Println("Audio data length:", len(audioData))

	client, err := getSpeechClient()
	if err != nil {
		return "", fmt.Errorf("failed to get client: %v", err)
	}

	config := &speechpb.RecognitionConfig{
		Encoding:        speechpb.RecognitionConfig_WEBM_OPUS,
		SampleRateHertz: 48000,
		LanguageCode:    "ja-JP",
	}

	audio := &speechpb.RecognitionAudio{
		AudioSource: &speechpb.RecognitionAudio_Content{
			Content: audioData,
		},
	}

	req := &speechpb.RecognizeRequest{
		Config: config,
		Audio:  audio,
	}

	ctx := context.Background()
	resp, err := client.Recognize(ctx, req)
	if err != nil {
		return "", fmt.Errorf("failed to recognize speech: %v", err)
	}

	// 認識結果を取得
	for _, result := range resp.Results {
		for _, alt := range result.Alternatives {
			// 最も精度の高い結果を返す
			return alt.Transcript, nil
		}
	}

	// 音声が認識されなかった場合
	log.Println("No result")
	return "", nil
}

func QueryGeminiAPI(w http.ResponseWriter, r *http.Request) {
	setResponseHeaders(w, r)

	// リクエストのパースを実行（必要に応じて）
	if err := r.ParseForm(); err != nil {
		http.Error(w, "error parsing form data.", http.StatusBadRequest)
		return
	}

	prompt := r.FormValue("prompt")
	if prompt == "" {
		http.Error(w, "no prompt.", http.StatusNotFound)
		return
	}

	res, err := queryVertexAIGeminiAPI(prompt)
	if err != nil {
		log.Println(fmt.Sprintf("server error: %s", err))
		http.Error(w, "error generating content.", http.StatusInternalServerError)
		return
	}
	log.Println(res)
}

func queryVertexAIGeminiAPI(inputText string) (string, error) {
	client, err := getGeminiClient()
	if err != nil {
		return "", fmt.Errorf("error creating client: %w", err)
	}

	ctx := context.Background()

	modelName := "gemini-1.5-pro"
	gemini := client.GenerativeModel(modelName)

	chat := gemini.StartChat()

	send := func(message string) (string, error) {
		r, err := chat.SendMessage(ctx, genai.Text(message))
		if err != nil {
			return "", fmt.Errorf("error sending message: %w", err)
		}

		var response string
		for _, candidate := range r.Candidates {
			for _, part := range candidate.Content.Parts {
				if t, ok := part.(genai.Text); ok {
					response += string(t)
				}
			}
			break
		}
		return response, nil
	}

	res, err := send("次の入力内容に対して以下のルールに従って返答してください。\n- 授業終了を表す内容が含まれていたら`quit`を返してください\n- 上記に当てはまらなかった場合には何も返さないでください\n入力内容にルールが複数回当てはまる場合、はじめに該当したルールに従って一回だけ返答してください。\nあなたの回答をプログラムが判定します。正確に返答するように注意してください。\n**返答には絶対に改行文字を含まないでください。**\nなお、この入力内容に対する返答はしないでください。")
	if err != nil {
		return "", fmt.Errorf("error creating client: %w", err)
	}

	res, err = send(inputText)
	if err != nil {
		return "", fmt.Errorf("error creating client: %w", err)
	}

	return res, nil
}
