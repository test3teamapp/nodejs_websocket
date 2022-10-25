package main

import (
	"crypto/rand"
	"fmt"
	"io/ioutil"
	"log"
	"mime"
	"net/http"
	"os"
	"path/filepath"

	socketio "github.com/googollee/go-socket.io"
)

const maxUploadSize = 2 * 1024 * 1024 // 2 MB
const uploadPath = "./tmp"

func randToken(len int) string {
	b := make([]byte, len)
	rand.Read(b)
	return fmt.Sprintf("%x", b)
}

func uploadFileMultipart(w http.ResponseWriter, r *http.Request) {
	fmt.Println("Multipart File Upload Endpoint Hit")

	// Parse our multipart form, 10 << 20 specifies a maximum
	// upload of 10 MB files.
	r.ParseMultipartForm(10 << 20)
	// FormFile returns the first file for the given key `myFile`
	// it also returns the FileHeader so we can get the Filename,
	// the Header and the size of the file
	file, handler, err := r.FormFile("myFile")
	if err != nil {
		fmt.Println("Error Retrieving the File")
		fmt.Println(err)
		return
	}
	defer file.Close()
	fmt.Printf("Uploaded File: %+v\n", handler.Filename)
	fmt.Printf("File Size: %+v\n", handler.Size)
	fmt.Printf("MIME Header: %+v\n", handler.Header)

	// Create a temporary file within our temp-images directory that follows
	// a particular naming pattern
	tempFile, err := ioutil.TempFile("temp-images", "upload-*.png")
	if err != nil {
		fmt.Println(err)
	}
	defer tempFile.Close()

	// read all of the contents of our uploaded file into a
	// byte array
	fileBytes, err := ioutil.ReadAll(file)
	if err != nil {
		fmt.Println(err)
	}
	// write this byte array to our temporary file
	tempFile.Write(fileBytes)
	// return that we have successfully uploaded our file!
	fmt.Fprintf(w, "Successfully Uploaded File\n")
}

func uploadHtmlFrontend(w http.ResponseWriter, r *http.Request) {
	fmt.Println("Html File Upload Frontend Hit")
	http.ServeFile(w, r, "htmlupload.html")
}
func uploadFileSocketIO(w http.ResponseWriter, r *http.Request) {
	fmt.Println("Html File Upload Frontend Hit")
	http.ServeFile(w, r, "htmlupload.html")
}

func setupRoutes() {
	http.HandleFunc("/uploadmultipart", uploadFileMultipart)
	http.HandleFunc("/uploadfrontend", uploadHtmlFrontend)

	server := socketio.NewServer(nil)

	server.OnConnect("/", func(s socketio.Conn) error {
		s.SetContext("")
		fmt.Println("connected:", s.ID())
		return nil
	})

	server.OnEvent("/", "notice", func(s socketio.Conn, msg string) {
		fmt.Println("notice:", msg)
		s.Emit("reply", "have "+msg)
	})

	server.OnEvent("/", "filesent", func(s socketio.Conn, file http.File) string {

		fileBytes, err := ioutil.ReadAll(file)
		if err != nil {
			return "INVALID_FILE"
		}

		detectedFileType := http.DetectContentType(fileBytes)
		switch detectedFileType {
		case "image/jpeg", "image/jpg":
		case "image/gif", "image/png":
		case "application/pdf":
			break
		default:
			return "INVALID_FILE_TYPE"
		}

		fileName := randToken(12)
		fileEndings, err := mime.ExtensionsByType(detectedFileType)
		if err != nil {
			return "CANT_READ_FILE_TYPE"
		}
		newPath := filepath.Join(uploadPath, fileName+fileEndings[0])
		fmt.Printf("FileType: %s, File: %s\n", detectedFileType, newPath)

		newFile, err := os.Create(newPath)
		if err != nil {
			return "CANT_CREATE_FILE"
		}
		defer newFile.Close()
		if _, err := newFile.Write(fileBytes); err != nil {
			return "CANT_WRITE_FILE"
		}

		fmt.Println("filesent:", "saved")
		return "recv "
	})

	server.OnEvent("/", "bye", func(s socketio.Conn) string {
		last := s.Context().(string)
		s.Emit("bye", last)
		s.Close()
		return last
	})

	server.OnError("/", func(s socketio.Conn, e error) {
		fmt.Println("meet error:", e)
	})

	server.OnDisconnect("/", func(s socketio.Conn, reason string) {
		fmt.Println("closed", reason)
	})

	go server.Serve()
	defer server.Close()

	http.Handle("/socket.io/", server)
	http.HandleFunc("/", uploadHtmlFrontend) // http.FileServer(http.Dir("./asset")))
	http.Handle("/nodejs", http.StripPrefix("/nodejs", http.FileServer(http.Dir("../node_modules/"))))
	log.Println("Serving at localhost:8083...")
	log.Fatal(http.ListenAndServe(":8083", nil))
}

func main() {
	fmt.Println("Hello World")
	setupRoutes()
}
