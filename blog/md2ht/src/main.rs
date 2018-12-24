use std::fs::File;

use std::io::{ self, Read };

use std::env::args;

struct SourceWalker {
	source: String,
	cursor: usize
}

impl SourceWalker {

	pub fn new(filename: &str) -> io::Result<SourceWalker> {	
		let mut file = File::open(filename)?;
		let mut source = String::new();
		file.read_to_string(&mut source)?;

		Ok(SourceWalker {
			source: source,
			cursor: 0
		})
	}

	pub fn eat(&mut self) -> Option<char> {	
		let next_character = self.peek();
		self.cursor += 1;
		next_character
	}

	pub fn munch(&mut self, count: usize) { 
		self.cursor += count;
	}

	pub fn peek(&self) -> Option<char> {
		self.peek_n(0)
	}

	pub fn peek_n(&self, offset: usize) -> Option<char> {
		self.source.chars().nth(self.cursor + offset)
	}

	/**
   * Consume until the next new line or EOF. Returns None if there is nothing left to be read.
   */
	pub fn eat_line(&mut self) -> Option<String> {
		if let Some(c) = self.peek() {
			let mut result = String::new();
			while let Some(c) = self.eat() {
				result += &c.to_string();
				if c == '\n' {
					break;
				}	
			}
			Some(result)
		} else {
			None
		}
	}

	/**
   * Consume all lines until the next empty line or line starting with a special character
   */
	pub fn eat_paragraph(&mut self) -> Option<String> {
		let mut result = None;
		while let Some(line) = self.eat_line() {

			let line = line.trim().to_string();

			//End loop if we read an empty line
			if line.len() == 0 {
				break;
			}

			if let Some(current) = result {
				result = Some(format!("{}\n{}", current, line));
			} else {
				result = Some(line);
			}
 
		}
		result
	}
}

fn is_code_block(walker: &mut SourceWalker) -> bool {
	const MARKER: Option<char> = Some('`');
	walker.peek_n(0) == MARKER && walker.peek_n(1) == MARKER && walker.peek_n(2) == MARKER
}

fn read_code_block(walker: &mut SourceWalker) -> String {
	walker.munch(3);

	let mut result = String::new();

	while let Some(c) = walker.peek() {

		if is_code_block(walker) {
			walker.munch(3);
			break;
		}

		result += &c.to_string();
		walker.eat();
	}

	result
}

fn read_list(walker: &mut SourceWalker) -> Vec<String> {
	let mut result = Vec::new();

	while let Some('*') = walker.peek() {
		walker.munch(1);

		if let Some(line) = walker.eat_line() {
			result.push(line.trim().to_string());
		}
	}

	result
}

fn main() -> io::Result<()> {

	let target_filename = args().nth(1).unwrap();
	let mut cursor = SourceWalker::new(&target_filename)?;

	while let Some(c) = cursor.peek() { 
		if c == '#' {
			let mut depth = 0;

			while let Some('#') = cursor.peek() {
				depth += 1;
				cursor.eat();
			}

			let heading = cursor.eat_paragraph().unwrap_or_else(|| "".to_string());
			println!("<h{}>{}</h{}>", depth, heading.trim(), depth);
		} else if c == '*' {
			let list_items = read_list(&mut cursor);
			println!("<ul>{}</ul>",
				list_items
					.iter()
					.map(|item| format!("<li>{}</li>", item))
					.fold(String::new(), |last, next| format!("{}{}", last, next))
			);
		} else if is_code_block(&mut cursor) {
			println!("<pre><code>{}</code></pre>", read_code_block(&mut cursor));
		} else {
			println!("<p>{}</p>", cursor.eat_paragraph().unwrap_or_else(|| "".to_string()));
		}
	}

	Ok(())
}
