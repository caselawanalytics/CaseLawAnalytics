import static org.leibnizcenter.rechtspraak.RechtspraakNlInterface.parseXml;
import static org.leibnizcenter.rechtspraak.RechtspraakNlInterface.requestXmlForEcli;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;

import javax.xml.bind.JAXBException;

import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.CommandLineParser;
import org.apache.commons.cli.DefaultParser;
import org.apache.commons.cli.HelpFormatter;
import org.apache.commons.cli.Option;
import org.apache.commons.cli.OptionGroup;
import org.apache.commons.cli.Options;
import org.apache.commons.cli.ParseException;
import org.leibnizcenter.rechtspraak.CouchInterface;

import generated.OpenRechtspraak;

public class RechtspraakXMLToJson {

	public static void main(String[] args) {
		// Command-line options: either ecli or input and output
		Options options = new Options();
		
		OptionGroup inputGroup = new OptionGroup();
		Option input = new Option("i", "input", true, "input file path");
		inputGroup.addOption(input);
		
		Option ecliStr = new Option("e", "ecli", true, "ECLI identifier");
		inputGroup.addOption(ecliStr);
		inputGroup.setRequired(true);
		options.addOptionGroup(inputGroup);
		
		Option output = new Option("o", "output", true, "output file");
		options.addOption(output);

		
		CommandLineParser parser = new DefaultParser();
		HelpFormatter formatter = new HelpFormatter();
        CommandLine cmd;

		try {
            cmd = parser.parse(options, args);
        } catch (ParseException e) {
            System.out.println(e.getMessage());
            formatter.printHelp("utility-name", options);

            System.exit(1);
            return;
        }
		if(cmd.hasOption('e')&&cmd.hasOption('i')){
			System.out.println("Provide either input file or ECLI identifier, not both.");
			formatter.printHelp("utility-name", options);
			System.exit(1);
            return;
		}
		
		//Read the options and call the right functions
		//Input XML and output path
		byte[] encodedXML;
		
		String outputPath;
		if(cmd.hasOption('e')){
			String ecli = cmd.getOptionValue('e');
			try {
				encodedXML = requestXmlForEcli(ecli).body().bytes();
			} catch(Exception e){
				System.out.println(e.getMessage());
				System.exit(1);
	            return;
			}
		}
		else if(cmd.hasOption('i')){
			try {
				encodedXML = Files.readAllBytes(Paths.get(cmd.getOptionValue('i')));
			} catch (IOException e) {
				System.out.println(e);
				System.exit(1);
	            return;
			}
		}
		else {
			System.out.println("Provide either input file or ECLI identifier.");
			formatter.printHelp("utility-name", options);
			System.exit(1);
            return;
		}
		if(cmd.hasOption('o')){
			String outputPathValue = cmd.getOptionValue('o');
			File file = new File(outputPathValue);
			if(file.isDirectory()){
				String filename;
				// If we have an ecli number, we use that as filename:
				if(cmd.hasOption('i')){
					filename = new File(cmd.getOptionValue('i')).getName();
					filename = filename.replaceAll(".xml$", ".json");
				}
				else {
					String ecli = cmd.getOptionValue('e');
					filename = ecli.replaceAll(":", "_")+".json";
				}
				outputPath = new File(outputPathValue, filename).getPath();
			}
			else {
				outputPath = cmd.getOptionValue('o');
			}
		}
		else if(cmd.hasOption('i')){
			String inputPath = cmd.getOptionValue('i');
			outputPath = inputPath.replaceAll(".xml$", ".json");
		}
		else {
			String ecli = cmd.getOptionValue('e');
			outputPath = ecli.replaceAll(":", "_")+".json";
		}
		
		//Do the actual conversion
		try {
			convertToJson(encodedXML, outputPath);
		} catch (JAXBException | IOException e) {
			System.out.println(e.getMessage());
			System.exit(1);
            return;
		}
		

	}
	
	public static void convertToJson(byte[] encodedXML, String outputPath) throws JAXBException, IOException{
		String strXml = new String(encodedXML, "UTF-8");
		//System.out.println(strXml);
		OpenRechtspraak doc = parseXml(strXml);

		String json = CouchInterface.toJson(doc);
		Files.write(Paths.get(outputPath), json.getBytes());
		System.out.println("Wrote JSON file to "+outputPath);
	}

}
