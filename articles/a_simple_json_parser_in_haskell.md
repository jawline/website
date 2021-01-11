!=!=! Title: Writing your own JSON parser in Haskell
!=!=! Created: 18-12-2020
!=!=! Tags: Projects

!=!=! Intro: Start
JSON (JavaScript object notation) is a ubiquitous text-based data format. To load JSON data into a program you need a JSON parser, a piece of code that reads the text JSON data and converts it into data structures that can be directly used by the program. In this article we walk through creating a JSON parser from scratch in Haskell.
!=!=! Intro: End

# TLDR;

Visit [this GitHub repository](https://github.com/jawline/JSON-Parser) for a simple JSON parser written in Haskell.

# Walkthrough

Before we get started we need to learn the format of the JSON language. Luckily, the website [json.org](https://www.json.org) has a thorough walkthrough, including text and visual representation of the format's grammar. To begin, we need to define a datastructure to hold the results of our JSON parser. This data-type needs to be capable of representing every valid JSON value. In Haskell, we use algebraic data-types for this:
```
data JSValue = JSObject (Map String JSValue)
  | JSArray [JSValue]
  | JSString String
  | JSNumber Double
  | JSBool Bool
  | JSNull
  deriving Show
```

This type, JSValue, is one of either an object (a map of JSValues), an array (A list of JSValues), a string (a list of character), a number (represented in Haskell as a double), a boolean, or null.

Note: We use String to represent JSON strings. This can be imported by `import Data.String (String)` under the module definition. We also use Map from the library containers to represent objects when parsing. This can be imported with `import Data.Map (Map, empty, insert)` added under the module definition.

Next, we need to define the skeleton of our parser. To demonstrate this, we will also define a rule for parsing `null` at the same time. To parse a JSON string we define the function `parseJson`, which takes a JSON encoded string and parses exactly one JSON value from it. The parseJson function will also return any characters that come after the parsed value, this will be used later when we parse arrays and objects. In Haskell, we define parseJson as:
```
parseJson :: String -> (JSValue, String)
```

To test this new method we will now write a parser for `null`, which should return a JSNull value. To parse `null` we will check if the string supplied is equal to the world null, and return JSNull if it is but return nothing if it is not. To represent this in Haskell we use the `Maybe` datatype, which allows us to specify that either a value of a specific type will be returned, or nothing will be. Like our new JSValue, Maybe is an algabraic datatype where `Just n` indicates a value has been returned and `Nothing` indicates that there is no result. The format for our `null` parsing function is this:
```
parseNull :: String -> Maybe (JSValue, String)
```
To implement it, we want to return JSNull if the JSON string is `null` but `Nothing` otherwise, so we use Haskell guards and the `isPrefixOf` method:
```
parseNull xs
  | isPrefixOf "null" xs = Just (JSNull, drop 4 xs)
  | otherwise = Nothing
```
This returns a value of JSNull only if the input string starts with the word "null", and returns Nothing otherwise. We also return the string after the word "null" by dropping four characters from the input string.

Note: To use isPrefixOf we need to import it from Data.List. We can do this by adding the following code under the module definition at the top of the program:
```
import Data.List (isPrefixOf)
```

To use this with our parseJson method we will also use a guard. In this guard we will return the result of parseNull only if parseNull is not Nothing. We do this by using the `Just x <- rhs` syntax, which will match the guard only if the expression on the right hand side resolves to the `Just` arm of the `Maybe` datatype, and it will bind the contents of `Just` to the variable named x. To use this in parseJson we can write:
```
parseJson xs
  | Just jsNull <- parseNull xs = jsNull
```

Now our parseJson method is capable of parsing the word null, but will error out if supplied with anything else. To test this we can write:
```
main :: IO ()
main = putStrLn (show (parseJson "null"))
```
Which should print:
```
(JSNull,"")
```

Now that we have the skeleton in place, we can quickly add support for booleans using the method:
```
parseBool :: String -> Maybe (JSValue, String)
parseBool xs
  | isPrefixOf "true" xs = Just (JSBool True, drop 4 xs)
  | isPrefixOf "false" xs = Just (JSBool False, drop 5 xs)
  | otherwise = Nothing
```
Like `parseNull` this returns something only if the JSON encoded string is a boolean, and if it does it also returns the characters after the string. It can be added in to parseJson by adding the additional rule `| Just jsBool <- parseBool = jsBool`. We can test this using the program:
```
main :: IO ()
main = do
  _ <- putStrLn (show (parseJson "null"))
  _ <- putStrLn (show (parseJson "false"))
  putStrLn (show (parseJson "true"))
```

Which gives the test output:
```
(JSNull,"")
(JSBool False,"")
(JSBool True,"")
``` 

### Parsing Numbers

Parsing numbers gets a little more complex, since we need to deal with '-' and fractions. In JSON, numbers are sequences of digits, which may be fractional (3123.44), and can be prefixed by a '-' to be made negative (-5432). To parse them, the first thing we need is a function to test if a character is a digit or not:
```
digit :: Char -> Bool
digit x = x >= '0' && x <= '9'
```
This method returns true if the character is a digit (0-9), and false otherwise. Next we define a function for parsing our numbers. Since a fractional number is defined as two integers, seperated by a dot, we begin by defining a function to parse an integer fragment, a series of uninterrupted digit characters (this would be matched by the regular expression /0-9*/):
```
extractInteger [] = ([], [])
extractInteger (x:xs)
  | digit x, (follows, xs) <- extractInteger xs = (x:follows, xs)
  | otherwise = ([], x:xs)
```
This function recursively consumes characters until a non-digit character is found, at which point it returns the tuple of (characters in the integer, characters after the integer). With this in place we now define a function to parse a JavaScript number:
```
parseDouble xs
  | ('-':xs) <- xs, (h, r) <- parseDouble xs = (-h, r) -- If our number starts with a - then negate it
  | ('.':xs) <- afterInteger, (fractionalPart, follows) <- extractInteger xs = (read (wholeInteger ++ "." ++ fractionalPart) :: Double, follows)
  | otherwise = (read wholeInteger :: Double, wholeInteger)
  where
    (wholeInteger, afterInteger) = extractInteger xs
```
This function has three rules. The first is straightforward, if the JSON string begins with a `-`, then parse the numeric value and negate it. If it is not a subtracted number, then we extract an integer from the JSON string `(wholeInteger, afterInteger) = extractInteger xs`. If the character that follows the extracted integer is a dot, then it is a number in the form `123.456` so we attempt to parse the fractional portion after the integer. Otherwise, we just use the integer portion. We use the built-in method read to convert the string representation of the number into a Haskell Double. Finally, we wire this all into our parseJson function through the function `parseNumber`, which tries to parse a number only if the JSON string begins with a `-` or a digit:
```
parseNumber xs
  | (head xs) == '-' || digit (head xs) = Just (JSNumber result, rest)
  | otherwise = Nothing
  where
    (result, rest) = parseDouble xs
```
We connect this to parseJson with the additional guard `| Just jsNum <- parseNumber xs = jsNum`. To test this we can use the program:
```
main :: IO ()
main = do
  _ <- putStrLn (show (parseJson "null"))
  _ <- putStrLn (show (parseJson "false"))
  _ <- putStrLn (show (parseJson "true"))
  _ <- putStrLn (show (parseJson "523"))
  _ <- putStrLn (show (parseJson "-5432.69"))
  _ <- putStrLn (show (parseJson "-96"))
```

### Parsing Strings

We can now move on to strings. JSON strings are sequences of zero or more characters in between opening and closing `"` characters. To extract this, we define the following function to extract up until the closing `"`:
```
parseStringInner :: String -> (String, String)
```

Naively, our implementation looks something like:
```
parseStringInner xs
  | ('"':xs) <- xs = ("", xs)
  | (x:xs) <- xs, (str, follows) <- parseStringInner xs = (x:str, follows)
```
Which we can then integrate into parseJson through the now predictable `parseString`:
```
parseString xs
  | ('"':xs) <- xs, (str, rest) <- parseStringInner xs = Just (JSString str, rest)
  | otherwise = Nothing
```
Unfortunately, this doesn't quite work because of escape characters, sequences of a '\' followed by a character which will map to something else. To implement escape characters we define the function `escaped :: Char -> Char`, which will map from the escape character to a different character. Our escaped function needs to include a rule for each valid JSON escape, and looks like:
```
escaped '"' = '"'
escaped '\\' = '\\'
escaped '/' = '/'
escaped 'b' = '\b'
escaped 'f' = '\f'
escaped 'r' = '\r'
escaped 'n' = '\n'
escaped 't' = '\t'
```
To integrate this into parseStringInner we add a new rule for sequences of a backslash followed by a character, which we map to this escaped function:
```
  | ('\\':r:xs) <- xs, (str, follows) <- parseStringInner xs = (escaped r:str, follows)
```
This should come before the final rule in parseStringInner, since that rule would also match the same sequence and Haskell pattern matches in the order that rules are defined.

With this all in place we should be able to execute programs like:
```
main :: IO ()
main = do
  _ <- putStrLn (show (parseJson "\"Hello\""))
  _ <- putStrLn (show (parseJson "\"Hello world \r\n\bQQQ 523\""))
```

### Parsing Arrays

We're now ready to move on to parsing JSON arrays. Arrays in JSON are comma seperated lists or JSON values, preceeded by a `[` and finished by a `]`. Since arrays contain lists of JSON values, we will need to recursively call parseJson for each item we find until the closing `]`. It is here that we can see why returning the unmatched portion of the string along with the JSValue in parseJson is useful, without it we would not be able to parse items in a list. To begin we define the function `parseArrayInner :: String -> ([JSValue], String)`, like `parseStringInner` this function is responsible for parsing until the closing `]`: 
```
parseArrayInner xs
  | (',':rest) <- rest, (recursed, recursedRest) <- parseArrayInner (skip rest) = (parsedItem:recursed, recursedRest)
  | (']':rest) <- rest = ([parsedItem], rest)
  where
    (parsedItem, rest) = parseJson xs
```
This function parses one JSON value from the JSON encoded string using the call to parseJson `(parsedItem, afterParsed) = parseJson xs`. It then follows one of two branches depending on the character that follows the item matched. If the character that follows is a ',' then the array is not finished, so we recurse. If the character that follows is a ']', then this is the last item in the array and we should terminate.

To wire this into parseJson we introduce the function `parseArray` which follows the same format as the other top level parsing methods. We define `parseArray` by:
```
parseArray xs
  | ('[':xs) <- xs, (']':xs) <- xs = Just (JSArray [], xs)
  | ('[':xs) <- xs, (arr, rest) <- parseArrayInner (skip xs) = Just (JSArray arr, rest)
  | otherwise = Nothing
```
This is similar to our other parsing methods, but also includes a rule for '[]', since arrays with zero elements are valid but would not be correctly handled otherwise. When integrated, we should be able to parse JSON strings like:
```
main = do
  _ <- putStrLn (show (parseJson "[1,2,3,4]"))
  _ <- putStrLn (show (parseJson "[1,2,[3,4]]"))
```

### Parsing Objects

Objects in JSON are very similar to arrays, but include a string key-name for each element. This leads to an almost identical flow but with a few more steps:
```
parseObjectInner xs
  | (',':rest) <- rest, (recursed, recursedRest) <- parseObjectInner rest = (insert parsedName parsedValue recursed, recursedRest)
  | ('}':rest) <- rest = (insert parsedName parsedValue empty, rest)
  where
    ('"':nameStart) = xs
    (parsedName, afterName) = parseStringInner nameStart
    (':':followingName) = skip afterName
    (parsedValue, afterValue) = parseJson followingName
    rest = skip afterValue

parseObject xs
  | ('{':xs) <- xs, ('}':xs) <- skip xs = Just (JSObject empty, xs)
  | ('{':xs) <- xs, (map, rest) <- parseObjectInner (skip xs) = Just (JSObject map, rest)
  | otherwise = Nothing
```
Here, we parse the `:` seperated key-name JSON value pairs from the JSON string and add them to the resulting map. The only thing introduced in this segment is the usage of `Map`. A fresh map is created by the function `empty`, for either empty objects or at the closing `}`. The method `insert` is used to add each item into the map as it is parsed. With this final parsing function we can now parse every JSON value, and should be able to execute programs like:
```
main = do
  _ <- putStrLn (show (parseJson "{\"items\":[1,2,3,{\"bob\":10}]}"))
``` 

### Skipping Whitespace

The final thing we have not addressed is how to deal with whitespace. Whitespace is allowed in JSON between any of the controlling characters (", :, {, }, [, ], etc) or any parsed value in arays and objects. To skip whitespace we define a function that drops any whitespace:
```
skip :: String -> String
skip [] = []
skip (' ':xs) = skip xs
skip ('\n':xs) = skip xs
skip ('\r':xs) = skip xs
skip ('\t':xs) = skip xs
skip xs = xs
```

We then need to call this function before any parsing step where whitespace should be ignored. Particularly, before parsing values or characters like ':' in arrays and objects. To use skip in `parseJson` we replace `parseJson` by `parseJsonInner` and call it using a new `parseJson` that skips whitespace:
```
parseJson :: String -> (JSValue, String)
parseJson xs = parseJsonInner (skip xs)
```
Skip also needs to be applied during parsing of arrays and objects. [An example implementation including all instances of skip can be found here on GitHub](https://github.com/jawline/JSON-Parser).
