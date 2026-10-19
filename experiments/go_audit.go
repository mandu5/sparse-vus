// Native semantic audit of the publicly released adscore package.
// Build in an isolated cache module; the upstream package stays unmodified.
package main

import (
    "encoding/json"
    "fmt"
    "os"
    "time"
    "github.com/stergiotis/boxer/public/analytics/timeseries/adscore"
)

type Input struct {
    Labels []bool `json:"labels"`
    Scores []float64 `json:"scores"`
    Buffer int32 `json:"buffer"`
    Repeats int `json:"repeats"`
}

func main() {
    var input Input
    if err := json.NewDecoder(os.Stdin).Decode(&input); err != nil { panic(err) }
    if input.Repeats < 1 { input.Repeats = 1 }
    seconds := make([]float64, input.Repeats)
    var result adscore.Measures
    for i := range input.Repeats {
        started := time.Now()
        var err error
        result, err = adscore.EvaluateE(input.Scores, input.Labels, input.Buffer)
        seconds[i] = time.Since(started).Seconds()
        if err != nil { panic(err) }
    }
    if err := json.NewEncoder(os.Stdout).Encode(map[string]any{"result": result, "seconds": seconds}); err != nil { fmt.Fprintln(os.Stderr, err); os.Exit(1) }
}
