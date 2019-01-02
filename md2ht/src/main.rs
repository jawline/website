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
		if let Some(_) = self.peek() {
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

	fn consume_paragraph(&mut self) -> String {

		let mut result = String::new();
		let mut current_line = String::new();

		while let Some(c) = self.peek() {

			if (c == '*' || c == '#' || self.is_intro_marker()) && current_line.len() == 0 {
				break;
			}

			if let Some(link) = self.consume_link() {
				current_line += &link;
			} else if c == '`' {
				current_line += &self.consume_inline_code_block();
			} else {
				self.munch(1);
				current_line += &c.to_string();
				if c == '\n' {
					result += &current_line;
					if current_line.len() < 2 {
						break;
					}
					current_line = String::new();
				}
			}
		}

		result
	}

	/**
	 * Methods for consuming links
	 */	

	/**
	 * Consume [...](...) and rewrite it to a link
	 */
	fn consume_link(&mut self) -> Option<String> {

		if self.peek() != Some('[') {
			return None;
		}

		let start_cursor = self.cursor;

		let mut name = String::new();
		let mut url = String::new();

		loop {
			let c = self.eat();
			match c {
				Some(c) => {
					name += &(c.to_string());
					if c == ']' { 
						break;
					}
				},
				None => {
					self.cursor = start_cursor;
					return None;
				}
			}
		}

		if self.peek() != Some('(') {
			self.cursor = start_cursor;
			return None;
		}

		loop {
			let c = self.eat();
			match c {
				Some(c) => {
					url += &(c.to_string());
					if c == ')' { 
						break;
					}
				},
				None => {
					self.cursor = start_cursor;
					return None;
				}
			}
		}

		Some(format!("<a href=\"{}\">{}</a>", &url[1..url.len() - 1], &name[1..name.len() - 1]))
	}

	/**
	 * Methods for consuming code blocks
	 */

	fn is_code_block(&self) -> bool {
		const MARKER: Option<char> = Some('`');
		self.peek_n(0) == MARKER && self.peek_n(1) == MARKER && self.peek_n(2) == MARKER
	}

	fn eat_code_block(&mut self) -> String {
		self.munch(3);
		let mut result = String::new();
		while let Some(c) = self.peek() {

			if self.is_code_block() {
				self.munch(3);
				break;
			}

			result += &c.to_string();
			self.eat();
		}

		result
	}

	fn consume_code_block(&mut self) -> String {
		format!("<pre><code>{}</code></pre>", self.eat_code_block())
	}

	fn consume_inline_code_block(&mut self) -> String {
		self.munch(1);
		let mut result = String::new();
		while let Some(c) = self.peek() {
			self.munch(1);
			if c == '`' { break; }
			result += &(c.to_string());
		}
		format!("<code>{}</code>", result)
	}

	/**
	 * Consume the intro header !!!!! ... !!!!! and rewrite to the <a-intro> flag
	 */

	fn is_intro_marker(&mut self) -> bool {
		for i in 0..5 {
			if self.peek_n(i) != Some('!') { 
				return false;
			}
		}
		true
	}

	fn consume_intro(&mut self) -> String {
		let mut result = String::new();
		while let Some(_) = self.peek() {
			if self.is_intro_marker() {
				self.munch(5);
				break;
			}
			result += &format!("<p>{}</p>", self.consume_paragraph());
		}
		format!("<a-intro>{}</a-intro>", result)
	}
	

	/** 
	 * Methods for consuming headings 
	 */

	fn consume_heading(&mut self) -> String {
		let mut depth = 0;

		while let Some('#') = self.peek() {
			depth += 1;
			self.eat();
		}

		let heading = self.eat_line().unwrap_or_else(|| "".to_string());
		format!("<h{}>{}</h{}><hr>", depth, heading.trim(), depth)
	}

	/**
	 * Methods for consuming MarkDown lists
	 */

	fn read_list(&mut self) -> Vec<String> {
		let mut result = Vec::new();

		while let Some('*') = self.peek() {
			self.munch(1);
			result.push(self.consume_paragraph().trim().to_string());
		}

		result
	}

	fn consume_list(&mut self) -> String {
		let list_items = self.read_list();
		format!("<ul>\n{}</ul>",
			list_items
				.iter()
				.map(|item| format!("\t<li>{}</li>\n", item))
				.fold(String::new(), |last, next| format!("{}{}", last, next))
		)
	}

	pub fn consume(&mut self) -> String {
		let mut result = String::new();

		while let Some(c) = self.peek() {

			if c == '#' {
				result = format!("{}\n{}", result, self.consume_heading());
			} else if c == '*' {
				result = format!("{}\n{}", result, self.consume_list());
			} else if self.is_intro_marker() {
				result = format!("{}\n{}", result, self.consume_intro());
			}  else if self.is_code_block() {
				result = format!("{}\n{}", result, self.consume_code_block());	
			} else if !c.is_whitespace() {
				result = format!("{}\n<p>{}</p>", result, self.consume_paragraph());
			} else {
				self.munch(1);
			}
		}

		result
	}

}



fn main() -> io::Result<()> {
	let target_filename = args().nth(1).unwrap();
	let mut cursor = SourceWalker::new(&target_filename)?;
	println!("{}", cursor.consume());
	Ok(())
}
