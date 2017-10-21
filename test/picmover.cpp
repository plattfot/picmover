#include <catch.hpp>
#include <picmover/picmover.hpp>

TEST_CASE("Filter and grouping")
{
  picmover::Files files = {"/path/test/image.nef",
                           "/path/test/image.raw",
                           "/path/test/file",
                           "/path/test/image0.jpeg",
                           "/path/test/image1.jpeg",
                           "/path/test/readme.txt"};

  SECTION("Filter out nothing")
  {
    auto all_files = std::move( picmover::filter( files, []( const picmover::fs::path& )
      {
        return true;
      } ));
    
    REQUIRE( all_files.size() == 6 );
  }
  
  SECTION("Filter out everything")
  {
    auto all_files = std::move( picmover::filter( files, []( const picmover::fs::path& )
      {
        return false;
      } ));
    
    REQUIRE( all_files.empty() );
  }

  SECTION("Filter out nef")
  {
    auto nef_files =
      std::move( picmover::filter( files, picmover::RegexFilter(std::regex("\\.nef")) ));
    
    REQUIRE( nef_files.size() == 1 );
  }

  SECTION("Filter out files with no extension")
  {
    auto ext_files =
      std::move( picmover::filter( files, picmover::RegexFilter(std::regex("\\..*")) ));
    
    REQUIRE( ext_files.size() == 5 );
  }

  SECTION("Group by extensions")
  {
    auto exts = 
      std::move( picmover::groupBy( files, []( const picmover::fs::path& file )
      {
        return file.has_extension() ? file.extension().string() : "unknown";
      }));
    
    REQUIRE( exts.size() == 5 );

    REQUIRE( exts["jpeg"].size() == 2 );
    REQUIRE( exts["nef"].size() == 1 );
    REQUIRE( exts["txt"].size() == 1 );
    REQUIRE( exts["raw"].size() == 1 );
    REQUIRE( exts["unknown"].size() == 1 );
  }
}

