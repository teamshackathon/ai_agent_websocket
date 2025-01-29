package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
)

const (
	FirebaseEmulatorAuthURL      = "http://localhost:9099"
	FirebaseEmulatorFirestoreURL = "http://localhost:8080"
	ProjectID                    = "demo-manabiya-ai"
)

// SignInResponse は Firebase Authentication のレスポンスを表します
type SignInResponse struct {
	IDToken string `json:"idToken"`
}

// signIn は Firebase Authentication Emulator にリクエストを送り、ID トークンを取得します
func signIn(email, password string) (*SignInResponse, error) {
	url := fmt.Sprintf("%s/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=any", FirebaseEmulatorAuthURL)

	requestBody, err := json.Marshal(map[string]interface{}{
		"email":            email,
		"password":         password,
		"returnSecureToken": true,
	})
	if err != nil {
		return nil, fmt.Errorf("リクエストボディの作成に失敗: %v", err)
	}

	resp, err := http.Post(url, "application/json", bytes.NewBuffer(requestBody))
	if err != nil {
		return nil, fmt.Errorf("ログインリクエスト失敗: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := ioutil.ReadAll(resp.Body)
		return nil, fmt.Errorf("ログイン失敗: %s", string(body))
	}

	var signInResp SignInResponse
	if err := json.NewDecoder(resp.Body).Decode(&signInResp); err != nil {
		return nil, fmt.Errorf("レスポンスのデコード失敗: %v", err)
	}

	fmt.Println("ログイン成功")
	return &signInResp, nil
}

// getDocumentFromFirestore は Firestore Emulator から指定されたドキュメントを取得します
func getDocumentFromFirestore(idToken, docPath string) (map[string]interface{}, error) {
	url := fmt.Sprintf("%s/v1/projects/%s/databases/(default)/documents/%s", FirebaseEmulatorFirestoreURL, ProjectID, docPath)

	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("リクエスト作成失敗: %v", err)
	}
	req.Header.Set("Authorization", "Bearer "+idToken)

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("Firestore リクエスト失敗: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := ioutil.ReadAll(resp.Body)
		return nil, fmt.Errorf("Firestore ドキュメント取得失敗: %s", string(body))
	}

	var document map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&document); err != nil {
		return nil, fmt.Errorf("レスポンスのデコード失敗: %v", err)
	}

	fmt.Println("Firestore ドキュメント取得成功:", document)
	return document, nil
}

func main() {
	email := "admin@manabiya.ai.com"
	password := "Manab1yaa1.Admin"

	// Firebase Authentication Emulator にログイン
	signInResp, err := signIn(email, password)
	if err != nil {
		fmt.Println("ログイン失敗:", err)
		return
	}

	// Firestore Emulator からドキュメント取得
	docPath := "notice/A2nNLNGl9oa7CYxPxcKB"
	document, err := getDocumentFromFirestore(signInResp.IDToken, docPath)
	if err != nil {
		fmt.Println("Firestore ドキュメント取得失敗:", err)
		return
	}

	fmt.Println("取得したドキュメント:", document)
}
