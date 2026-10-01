// Instalador .exe del Cargador de datos a SAC.
//
// Lleva adentro (go:embed) el paquete: la aplicación con sus librerías, los
// scripts de instalación y, salvo en la versión liviana, Node.js portátil. Al
// ejecutarlo lo extrae en una carpeta temporal y corre
// Instalar-CargadorSAC-Usuario.ps1, que instala para el usuario actual sin
// permisos de administrador.
//
// Los argumentos se pasan tal cual al script, p. ej.:
//
//	Instalar-CargadorSAC-Fanalca.exe -Puerto 3005 -Reconfigurar
//
// Se compila con ../build-exe.js (no directamente con go build).
package main

import (
	"archive/zip"
	"bufio"
	"bytes"
	_ "embed"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
)

//go:embed payload.zip
var payload []byte

func extract(dst string) error {
	r, err := zip.NewReader(bytes.NewReader(payload), int64(len(payload)))
	if err != nil {
		return err
	}
	base := filepath.Clean(dst) + string(os.PathSeparator)
	for _, f := range r.File {
		target := filepath.Join(dst, filepath.FromSlash(f.Name))
		if !strings.HasPrefix(target, base) {
			return fmt.Errorf("ruta no permitida en el paquete: %s", f.Name)
		}
		if f.FileInfo().IsDir() {
			if err := os.MkdirAll(target, 0o755); err != nil {
				return err
			}
			continue
		}
		if err := os.MkdirAll(filepath.Dir(target), 0o755); err != nil {
			return err
		}
		if err := writeFile(f, target); err != nil {
			return err
		}
	}
	return nil
}

func writeFile(f *zip.File, target string) error {
	in, err := f.Open()
	if err != nil {
		return err
	}
	defer in.Close()
	out, err := os.OpenFile(target, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0o644)
	if err != nil {
		return err
	}
	if _, err := io.Copy(out, in); err != nil {
		out.Close()
		return err
	}
	return out.Close()
}

func pause() {
	if os.Getenv("CARGADOR_SIN_PAUSA") != "" {
		return
	}
	fmt.Print("\nPresione Enter para cerrar esta ventana...")
	bufio.NewReader(os.Stdin).ReadString('\n')
}

func run() int {
	fmt.Println("Preparando el instalador del Cargador de datos a SAC...")
	tmp, err := os.MkdirTemp("", "CargadorSAC-")
	if err != nil {
		fmt.Println("ERROR: no se pudo crear la carpeta temporal:", err)
		return 1
	}
	defer os.RemoveAll(tmp)

	if err := extract(tmp); err != nil {
		fmt.Println("ERROR: no se pudo extraer el paquete:", err)
		return 1
	}
	script := filepath.Join(tmp, "CargadorSAC-Instalador", "instalador", "Instalar-CargadorSAC-Usuario.ps1")

	// CARGADOR_POWERSHELL sólo se usa para probar el .exe fuera de Windows.
	shell := os.Getenv("CARGADOR_POWERSHELL")
	if shell == "" {
		if runtime.GOOS == "windows" {
			shell = "powershell.exe"
		} else {
			shell = "pwsh"
		}
	}
	args := append([]string{"-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script}, os.Args[1:]...)
	cmd := exec.Command(shell, args...)
	cmd.Stdin, cmd.Stdout, cmd.Stderr = os.Stdin, os.Stdout, os.Stderr
	if err := cmd.Run(); err != nil {
		if ee, ok := err.(*exec.ExitError); ok {
			return ee.ExitCode()
		}
		fmt.Println("ERROR: no se pudo ejecutar PowerShell:", err)
		return 1
	}
	return 0
}

func main() {
	code := run()
	pause()
	os.Exit(code)
}
