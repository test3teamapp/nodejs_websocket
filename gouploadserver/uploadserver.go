package main

import (
	"crypto/rand"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"time"
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

	if handler.Size > maxUploadSize {
		fmt.Println("Error: File to big !")
		return
	}

	// Create a temporary file within our temp-images directory that follows
	// a particular naming pattern
	tempFile, err := ioutil.TempFile(uploadPath, "upload-*.png")
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

func timeHandler(w http.ResponseWriter, r *http.Request) {
	fmt.Fprint(w, time.Now().Format("02 Jan 2006 15:04:05 MST"))
}

func fileServerHandler(w http.ResponseWriter, r *http.Request) {

	fmt.Println("fileServerHandlert : ", r.Host, r.URL.Path)

	files, err := ioutil.ReadDir("./tmp")
	if err != nil {
		log.Fatal(err)
		return
	}

	w.WriteHeader(http.StatusOK)

	for _, file := range files {
		fmt.Fprintf(w, "%s dir: %v  %d\n", file.Name(), file.IsDir(), file.Size())
	}
}

func setupRoutes() {
	http.HandleFunc("/uploadmultipart", uploadFileMultipart)
	http.HandleFunc("/uploadfrontend", uploadHtmlFrontend)
	http.HandleFunc("/uploaddir", fileServerHandler) //http.FileServer(http.Dir("./tmp")))
	http.HandleFunc("/servetime", timeHandler)
	log.Println("Upload server at localhost:8083...")
	log.Fatal(http.ListenAndServe(":8083", nil))
}

func main() {
	fmt.Println("Hello World")
	setupRoutes()
}
