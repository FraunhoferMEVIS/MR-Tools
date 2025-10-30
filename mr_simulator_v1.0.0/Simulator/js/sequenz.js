
export function readSequence(file) {

    const rfPulseList = [];

    function isTxtFile(file){
        return file.name.toLowerCase().endsWith('.txt');
    }

    if(isTxtFile(file)===true){
        // file ist ein File-Objekt aus dem Browser, NICHT ein Dateipfad
        const reader = new FileReader();
        
        reader.onload = function(event) {
            try {
                const data = event.target.result;
                
                // Jede Zeile enthält ein JSON-Objekt -> Split nach Zeilenumbrüchen
                const lines = data.split('\n').filter(line => line.trim() !== '');

                console.log(`Datei gelesen: ${file.name}`);
                console.log(`Anzahl Zeilen: ${lines.length}`);

                lines.some((line, index) => {
                    try {
                        var jsonObj = JSON.parse(line);  // JSON-String in Objekt umwandeln
                        console.log(`\n=== Objekt ${index + 1} ===`);
                        
                        for(var event in jsonObj){
                            switch(event){

                                case "rf_id":
                                    if(jsonObj[event] =! 0){
                                        rfPulseList.push(jsonObj["rf_am"]);
                                        console.log("RF-Pulse:", jsonObj["rf_am"]);
                                    } 
                                    break;
                            }
                        }
                        
                    
                        return true //bei true ist es nur ein durchlauf, bei false geht es weiter (hier nur true zum test des ersten RF-Pulse)
                    }

                     catch (e) {
                        console.error(`Fehler beim Parsen der Zeile ${index + 1}:`, e);
                        console.error(`Zeile Inhalt: "${line}"`);
                        alert("Selected data is not a sequence");
                        return true
                    }
                });
            } catch (error) {
                console.error('Fehler beim Lesen der Datei:', error);
            }

        };
        
        reader.onerror = function(error) {
            console.error('FileReader Fehler:', error);
        };
        
        // Datei als Text lesen
        reader.readAsText(file);
        
        }

        else{
            alert("Not a txt data")
        }
    return rfPulseList
}