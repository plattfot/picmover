#include "picmover.hpp"

namespace picmover {
inline
namespace PICMOVER_VERSION_STR {

  auto RegexFilter::operator()( const fs::path& file ) const -> bool
  {
    return std::regex_search( file.string(), m_regex );
  }

} // namespace vX_Y
} // namespace picmover...
